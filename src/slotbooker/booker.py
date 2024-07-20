import os
import logging
import yaml
from selenium.common.exceptions import SessionNotCreatedException, NoSuchDriverException

from .utils.driver import close_driver, get_driver
from .utils.custom_logger import LogHandler
from .utils.mailhandler import MailHandler
from .ui_interaction import Booker

# Load configuration files
config_path = os.path.join(os.path.dirname(__file__), "utils/config.yaml")
with open(config_path, "r") as file:
    config = yaml.safe_load(file)

classes_path = os.path.join(os.path.dirname(__file__), "data/classes.yaml")
with open(classes_path, "r") as file:
    classes = yaml.safe_load(file)

env_vars_to_check = [
    "OCTIV_USERNAME",
    "OCTIV_PASSWORD",
    "DAYS_BEFORE_BOOKABLE",
    "EXECUTION_BOOKING_TIME",
]
# Create an instance of ClassVarHelper
# helper = ClassVarHelper(env_vars_to_check)
# helper.check_vars()


def main(retry: int = 3):
    """Slotbooker Main Function.

    This function represents the main flow of the Slotbooker application. It performs the following steps:
    - Starts writing output to a logfile using 'setup_log_dir'.
    - Retrieves environment variables 'OCTIV_USERNAME' and 'OCTIV_PASSWORD'.
    - If the required environment variables are not set, it informs the user to set them.
    - If the environment variables are set, it initializes a web driver and logs into the website.
    - Switches to the desired day and books a slot according to the configuration.
    - Closes the web driver after completing the booking process.
    - Sends the log file to an email address using 'send_logs_to_mail'.

    Returns:
        None: This function does not return anything.

    Example:
        Run this function to perform the slot booking process with the configured options:

        >>> main()
    """
    log_hander = LogHandler()
    driver = get_driver(chromedriver=config.get("chromedriver"))

    if os.environ.get("IS_TEST"):
        logging.info("Testing Docker Container")
        booker = Booker(
            driver=driver,
            days_before_bookable=0,
            base_url=config.get("base_url"),
            execution_booking_time="00:00:00.00",
        )
        user = os.environ.get("OCTIV_USERNAME")
        password = "if-this-would-be-the-password"

        login_failed = booker.login(username=user, password=password)
        if login_failed:
            logging.success(message="TEST OK | Login failed as expected")

        exit()

    # Retrieve environment variables
    user = os.environ.get("OCTIV_USERNAME")
    password = os.environ.get("OCTIV_PASSWORD")
    days_before_bookable = int(os.environ.get("DAYS_BEFORE_BOOKABLE", 0))
    execution_booking_time = os.environ.get("EXECUTION_BOOKING_TIME")
    booked_successful = False

    logging.info(f"Log in as: {user}")

    for attempt in range(1, retry + 1):
        try:
            booker = Booker(
                driver=driver,
                days_before_bookable=days_before_bookable,
                base_url=config.get("base_url"),
                execution_booking_time=execution_booking_time,
            )

            booker.login(username=user, password=password)
            booker.switch_day()
            booked_successful, class_slot, time_slot = booker.book_class(
                class_dict=classes.get("class_dict"),
                booking_action=classes.get("book_class"),
            )

            close_driver(driver)
            logging.success(f"Attempt {attempt}: OctivBooker succeeded")
            response = "SUCCESS"
            break
        except (SessionNotCreatedException, NoSuchDriverException) as e:
            logging.warning(
                f"Attempt {attempt}: OctivBooker failed due to driver issue"
            )
            logging.error(e, exc_info=True)
        except Exception as e:
            logging.warning(
                f"Attempt {attempt}: OctivBooker failed due to unexpected error"
            )
            logging.error(e, exc_info=True)

    html_file = log_hander.convert_logs_to_html()

    mail_handler = MailHandler(format="html")
    if booked_successful:
        response = "Success"
        mail_handler.send_logs_to_mail(filename=html_file, response=response)
        mail_handler.send_successful_booking_email(
            time_slot, class_slot
        )
    else:
        mail_handler.send_unsuccessful_booking_email()
        response = "Failed"
        mail_handler.send_logs_to_mail(filename=html_file, response=response)


if __name__ == "__main__":
    main()
