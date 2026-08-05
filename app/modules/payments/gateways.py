"""
Payment gateway abstraction. Each provider implements `create_payment` and
`verify_webhook`; the service layer never talks to razorpay/stripe SDKs directly.
Fill in provider credentials via app.core.config.settings.* and the real SDK
calls (razorpay-python, stripe, PhonePe S2S API) here.
"""
from abc import ABC, abstractmethod


class PaymentGateway(ABC):
    @abstractmethod
    def create_payment_intent(self, amount: int, currency: str, receipt: str) -> dict:
        """Returns provider-specific data the frontend/mobile SDK needs to collect payment."""

    @abstractmethod
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        ...


class RazorpayGateway(PaymentGateway):
    def create_payment_intent(self, amount: int, currency: str, receipt: str) -> dict:
        # import razorpay; client = razorpay.Client(auth=(key_id, key_secret)); client.order.create(...)
        return {"provider": "razorpay", "amount": amount, "currency": currency, "receipt": receipt}

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        return True  # replace with razorpay.utility.verify_webhook_signature


class StripeGateway(PaymentGateway):
    def create_payment_intent(self, amount: int, currency: str, receipt: str) -> dict:
        return {"provider": "stripe", "amount": amount, "currency": currency, "receipt": receipt}

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        return True


class PhonePeGateway(PaymentGateway):
    def create_payment_intent(self, amount: int, currency: str, receipt: str) -> dict:
        return {"provider": "phonepe", "amount": amount, "currency": currency, "receipt": receipt}

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        return True


GATEWAYS: dict[str, PaymentGateway] = {
    "razorpay": RazorpayGateway(),
    "stripe": StripeGateway(),
    "phonepe": PhonePeGateway(),
}


def get_gateway(provider: str) -> PaymentGateway:
    gateway = GATEWAYS.get(provider)
    if not gateway:
        raise ValueError(f"Unsupported payment provider: {provider}")
    return gateway
