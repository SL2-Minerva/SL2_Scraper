def is_timeout(e):
    # รอข้อมูลนานเกิน 30 วินาที
    return "timeout" in str(e) or "timed out" in str(e) or "Timeout" in str(e)


def is_invalid_session_id(e):
    # ไม่พบ session id ปัจจุบัน
    return "invalid session id" in str(e)


def is_unknown_error(e):
    return "unknown error" in str(e)


def is_error_name_not_resolved(e):
    return "ERR_NAME_NOT_RESOLVED" in str(e)


def is_page_crash(e):
    # เว็บไซต์ปลายทางไม่ตอบสนองในขณะนี้ กรุณาลองใหม่อีกครั้งภายหลัง 5 - 10 นาที
    return "session deleted because of page crash" in str(e)


def is_connection_db_error(e):
    return "Connection refused, Timeout" in str(e)


def is_max_retries_url(e):
    # มีคนใช้งานเยอะเกินไป กรุณาลองใหม่อีกครั้งภายหลัง 5 - 10 นาที
    return "Max retries exceeded" in str(e)


def handle(e):
    result = {
        "is_error": False,
        "message": ""
    }

    if is_connection_db_error(e):
        result["message"] = "ไม่สามารถเชื่อมต่อฐานได้"
    elif is_invalid_session_id(e):
        result["message"] = "ไม่พบ session id ปัจจุบัน"
    elif is_timeout(e):
        result["message"] = "รอข้อมูลนานเกิน 30 วินาที"
    elif is_page_crash(e) or is_unknown_error(e):
        result["message"] = "เว็บไซต์ปลายทางไม่ตอบสนองในขณะนั้น"
    elif is_max_retries_url(e) or is_error_name_not_resolved(e):
        result["message"] = "มีการส่ง Request เยอะเกินไปในขณะนั้น"
    else:
        result["message"] = f"ส่งถึง Developer\n\n{str(e)}"

    result["is_error"] = result["message"] != ""

    return result
