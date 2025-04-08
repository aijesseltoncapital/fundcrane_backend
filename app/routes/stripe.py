from flask import Blueprint, request, jsonify
import stripe
from app.config import Config

stripe.api_key = Config.STRIPE_SECRET_KEY
payments_bp = Blueprint('payments', __name__)

@payments_bp.route('/create-subscription-product', methods=['POST'])
def create_subscription_product():
    try:
        data = request.get_json()
        
        # Validate input
        amount = data.get('amount')  # Monthly amount in cents
        investment_amount = data.get('investmentAmount')  # Total investment amount in cents
        currency = data.get('currency', 'sgd')
        customer_name = data.get('customerName', '')

        if not amount or not investment_amount:
            return jsonify({'error': 'Amount and Investment Amount are required'}), 400

        # Create a Stripe Product for the investment
        product = stripe.Product.create(
            name=f"Investment Installment Plan - {customer_name}",
            metadata={
                'total_investment_amount': str(investment_amount),
                'monthly_amount': str(amount),
                'customer_name': customer_name
            }
        )

        # Create a Price for the Product (monthly recurring)
        price = stripe.Price.create(
            product=product.id,
            unit_amount=amount,
            currency=currency,
            recurring={
                'interval': 'month',
                'interval_count': 1  # Monthly
            }
        )

        return jsonify({
            'productId': product.id,
            'priceId': price.id
        })

    except stripe.error.StripeError as e:
        return jsonify({
            'error': str(e)
        }), 403
    except Exception as e:
        return jsonify({
            'error': 'An unexpected error occurred'
        }), 500

@payments_bp.route('/create-subscription', methods=['POST'])
def create_subscription():
    try:
        data = request.get_json()
        
        # Validate input
        price_id = data.get('priceId')
        customer_name = data.get('customerName', '')
        payment_method_type = data.get('paymentMethodType', 'card')
        payment_method_id = data.get('paymentMethodID')
        print('paymentID ',payment_method_id)
        
        if not price_id:
            return jsonify({'error': 'Price ID is required'}), 400

        # Retrieve the associated price to get product details
        price = stripe.Price.retrieve(price_id)
        product = stripe.Product.retrieve(price.product)
        print('priceID retrived',price_id)

        # Create a Customer
        customer = stripe.Customer.create(
            name=customer_name,
            metadata={
                'total_investment_amount': product.metadata.get('total_investment_amount', ''),
                'monthly_amount': product.metadata.get('monthly_amount', '')
            },
            payment_method = payment_method_id
        )
        stripe.Customer.modify(
            customer.id,
            invoice_settings = {'default_payment_method': payment_method_id}
        )
        print('customer created',customer.id)

        # Create a Subscription
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{
                'price': price_id,
            }],
            payment_settings={
                'payment_method_types': [payment_method_type],
                'save_default_payment_method': 'on_subscription'
            },
            metadata={
                'product_id': product.id,
                'total_investment_amount': product.metadata.get('total_investment_amount', ''),
                'monthly_amount': product.metadata.get('monthly_amount', '')
            },
        )
        print('sub created') # Create a payment method and attach it to the customer

        # Create a PaymentIntent for the first payment confirmation
        payment_intent = stripe.PaymentIntent.create(
            amount=int(product.metadata.get('monthly_amount', 0)),
            currency='sgd',
            customer=customer.id,
            payment_method_types=['card'],
            metadata={
                'subscription_id': subscription.id,
                'is_first_installment': 'true'
            }
        )
        print('intent created')

        return jsonify({
            'subscriptionId': subscription.id,
            'clientSecret': payment_intent.client_secret,
            'customerId': customer.id
        })

    except stripe.error.StripeError as e:
        return jsonify({
            'error': str(e)
        }), 403
    except Exception as e:
        return jsonify({
            'error': 'An unexpected error occurred'
        }), 500

@payments_bp.route('/create-payment-intent', methods=['POST'])
def create_payment_intent():
    try:
        data = request.get_json()
        
        # Validate input
        amount = data.get('amount')
        currency = data.get('currency', 'sgd')
        
        if not amount:
            return jsonify({'error': 'Amount is required'}), 400

        # Metadata for installment tracking
        metadata = data.get('metadata', {})
        
        # Create a PaymentIntent
        payment_intent = stripe.PaymentIntent.create(
            amount=amount,  # amount in cents
            currency=currency,
            payment_method_types=['card'],
            metadata=metadata
        )

        return jsonify({
            'clientSecret': payment_intent.client_secret
        })

    except stripe.error.StripeError as e:
        return jsonify({
            'error': str(e)
        }), 403
    except Exception as e:
        return jsonify({
            'error': 'An unexpected error occurred'
        }), 500
    
# Enhanced webhook for handling various payment events
@payments_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET')
        )
    except ValueError:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        return 'Invalid signature', 400

    # Handle specific event types
    if event.type == 'payment_intent.succeeded':
        payment_intent = event.data.object
        metadata = payment_intent.metadata

        # Log or process installment details
        if metadata.get('is_first_installment') == 'true':
            print(f"First installment payment received: {metadata}")
            # Additional logic for first installment tracking

    elif event.type == 'invoice.paid':
        invoice = event.data.object
        subscription_id = invoice.subscription

        # Log successful monthly payment
        print(f"Invoice paid for subscription: {subscription_id}")
        # You could trigger additional logic here, like:
        # - Recording the payment
        # - Updating user's investment status

    elif event.type == 'subscription_schedule.completed':
        subscription_schedule = event.data.object
        print(f"Subscription schedule completed: {subscription_schedule.id}")
        # Handle end of 12-month subscription

    return 'Success', 200