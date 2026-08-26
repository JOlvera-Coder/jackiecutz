import logging

logger = logging.getLogger(__name__)

class DispatchManager:
    @staticmethod
    def send_sms(to_phone: str, message: str) -> bool:
        logger.info(f"[DISPATCH] To: {to_phone} - Message: {message}")
        print(f"\n📨 [SMS TO {to_phone}]: {message}\n")
        return True

    @classmethod
    def notify_booking_confirmed(cls, booking):
        msg = f"JackieCutz: Hey {booking.customer.name}, your {booking.service.name} is confirmed for {booking.scheduled_time.strftime('%a, %b %d at %I:%M %p')}."
        return cls.send_sms(booking.customer.phone, msg)

    @classmethod
    def notify_next_in_line(cls, booking):
        msg = f"JackieCutz: Hey {booking.customer.name}! Jackie is finishing up—you are next in the chair. Please head inside."
        return cls.send_sms(booking.customer.phone, msg)