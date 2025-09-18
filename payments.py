# payments.py

import os
import stripe
from flask import (
    Blueprint, request, redirect, url_for,
    render_template, current_app, jsonify,
    session, flash
)
from flask_login import login_required, current_user
from models import db, User, FREE_TIER_LIMIT

# ─── Stripe Initialization ───────────────────────────────────────────────
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
if not stripe.api_key:
    raise RuntimeError("Missing STRIPE_SECRET_KEY in environment")

ONE_TIME_PRICE_ID      = os.environ.get('STRIPE_ONE_TIME_PRICE_ID')
SUBSCRIPTION_PRICE_ID  = os.environ.get('STRIPE_SUBSCRIPTION_PRICE_ID')
STRIPE_WEBHOOK_SECRET  = os.environ.get('STRIPE_WEBHOOK_SECRET')

# Define your premium limit here (keep in sync with app.py)
PREMIUM_TIER_LIMIT     = 50

payments = Blueprint('payments', __name__, template_folder='templates')


@payments.route('/upgrade', methods=['GET'])
@login_required
def upgrade():
    """
    Show the upgrade page where the user picks one-time vs subscription.
    """
    publishable_key = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    return render_template(
        'upgrade.html',
        stripe_public_key=publishable_key,
        one_time_price_id=ONE_TIME_PRICE_ID,
        subscription_price_id=SUBSCRIPTION_PRICE_ID
    )


@payments.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """
    Called by the upgrade.html form.  Creates a Stripe checkout session
    for either one-time or subscription, and carries forward our draft project_id.
    """
    plan = request.form.get('plan_type')
    if plan == 'one_time':
        price_id = ONE_TIME_PRICE_ID
        mode     = 'payment'
    elif plan == 'subscription':
        price_id = SUBSCRIPTION_PRICE_ID
        mode     = 'subscription'
    else:
        return "Invalid plan selected", 400

    proj_id = session.get('pending_project_id')
    if not proj_id:
        return "No project to resume after payment", 400

    try:
        chk = stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode=mode,
            line_items=[{'price': price_id, 'quantity': 1}],
            success_url=(
                url_for('payments.success', _external=True)
                + '?session_id={CHECKOUT_SESSION_ID}'
            ),
            cancel_url=url_for('payments.cancel', _external=True),
            client_reference_id=str(current_user.id),
            metadata={'project_id': str(proj_id)}
        )
        return redirect(chk.url, code=303)
    except Exception as e:
        current_app.logger.error(f"Stripe checkout failed: {e}")
        return jsonify(error=str(e)), 500


@payments.route('/success')
@login_required
def success():
    """
    After Stripe redirects back, mark the user premium (in case webhook is slow),
    then resume the draft project.
    """
    sess_id = request.args.get('session_id')
    if not sess_id:
        flash("No session ID provided", "error")
        return redirect(url_for('payments.upgrade'))

    try:
        checkout_sess = stripe.checkout.Session.retrieve(sess_id)
    except Exception as e:
        current_app.logger.error(f"Error retrieving session: {e}")
        flash("Error verifying payment", "error")
        return redirect(url_for('payments.upgrade'))

    if checkout_sess.payment_status not in ('paid', 'complete'):
        flash("Payment was not completed", "error")
        return redirect(url_for('payments.upgrade'))

    # mark user premium AND give them a non-NULL projects_limit
    user = User.query.get(int(checkout_sess.client_reference_id))
    if user and not user.is_premium:
        user.is_premium      = True
        user.projects_limit  = PREMIUM_TIER_LIMIT
        db.session.commit()
        current_app.logger.info(f"User {user.email} upgraded via success redirect")

    # resume the project
    proj_id = checkout_sess.metadata.get('project_id') or session.pop('pending_project_id', None)
    if proj_id:
        flash("Upgrade successful! Resuming your video…", "success")
        return redirect(url_for('clips', project_id=proj_id))

    # fallback
    return render_template('payment_success.html')


@payments.route('/cancel')
@login_required
def cancel():
    """Landing page if user cancels checkout."""
    return render_template('payment_cancelled.html')


@payments.route('/webhook', methods=['POST'])
def webhook_received():
    """
    Official Stripe webhook handler.  Marks users premium if they convert.
    """
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        current_app.logger.error(f"Webhook error: {e}")
        return '', 400

    if event['type'] == 'checkout.session.completed':
        session_obj = event['data']['object']
        uid     = session_obj.get('client_reference_id')
        try:
            user = User.query.get(int(uid))
            if user and not user.is_premium:
                user.is_premium      = True
                user.projects_limit  = PREMIUM_TIER_LIMIT
                db.session.commit()
                current_app.logger.info(f"User {user.email} upgraded via webhook")
        except Exception as e:
            current_app.logger.error(f"Webhook DB update failed: {e}")

    return '', 200