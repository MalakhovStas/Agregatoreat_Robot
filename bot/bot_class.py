import time
from time import sleep
from typing import List

from pywinauto.application import Application
from selenium.common.exceptions import StaleElementReferenceException, ElementClickInterceptedException, \
    TimeoutException, InvalidSelectorException
from selenium.webdriver import Chrome, ActionChains, Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.remote.webelement import WebElement
from config import MAIN_URL, TRADES_URL, LOGIN_URL
from database import Controller
from colorama import init, Fore


class Logs:
    def __init__(self, work: bool):
        self.LOG_FMT = '{time:DD-MM-YYYY at HH:mm:ss} | {level: <8} | line: {line: >3} | message: {message}'
        # func: {function: ^ 15} |
        self.work = work

    def logger(self, level: str, message):
        if self.work:
            from loguru import logger
            logger.add(sink='logs/debug.log', format=self.LOG_FMT, level='TRACE', diagnose=True, backtrace=False,
                       rotation="100 MB", retention=2, compression="zip")
            if level.lower() == 'info':
                return logger.info(message)
            elif level.lower() == 'debug':
                return logger.debug(message)
            elif level.lower() == 'warning':
                return logger.warning(message)
            elif level.lower() == 'trace':
                return logger.trace(message)


my_logger = Logs(work=False)


class Bot:
    def __init__(self, mail: str, password: str, certificate_name: str, tin: str, keyword: str, first_desc: str,
                 second_desc: str, bets_to_exclude: str, purchase_number: str, only_EAT: str, automatic_sbsc: str,
                 name_org_client: str, wait_time: int = 20, error_time: int = 1, cards_time: int = 3):
        self.service = Service(executable_path=ChromeDriverManager().install())
        self.options = Options()
        self.options.add_experimental_option("excludeSwitches", ['enable-automation'])
        self.options.add_argument('start-maximized')
        self.options.add_extension('plugin.crx')
        self.driver: Chrome = Chrome(service=self.service, options=self.options)
        self.waiter: WebDriverWait = WebDriverWait(self.driver, wait_time)
        self.error_waiter: WebDriverWait = WebDriverWait(self.driver, error_time)
        self.cards_waiter: WebDriverWait = WebDriverWait(self.driver, cards_time)
        self.actions: ActionChains = ActionChains(self.driver)
        self.mail = mail.strip()
        self.password = password.strip()
        self.certificate_name = certificate_name.strip()
        self.tin = tin.strip()
        self.name_org_client = name_org_client.strip()
        self.keyword = keyword.strip()
        self.first_desc = first_desc.strip()
        self.second_desc = second_desc.strip()
        self.bets_to_exclude: list = [int(bet_to_exclude) for bet_to_exclude in
                                      bets_to_exclude.split() if len(bet_to_exclude) and bet_to_exclude.isdigit()]
        self. purchase_number = purchase_number.strip()
        self.only_EAT = int(only_EAT.strip()) if only_EAT.strip().isdigit() else 0
        self.automatic_sbsc = automatic_sbsc

    def login(self):
        """Вводит логин и пароль"""
        my_logger.logger('debug', 'start funk -> login')

        self.driver.get(LOGIN_URL)
        login_input = self.waiter.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[name="Username"]')))
        login_input.send_keys(self.mail)

        password_input = self.waiter.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[name="Password"]')))
        password_input.send_keys(self.password)

        login_button = self.waiter.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '#loginForm > fieldset > button')))
        login_button.click()

        self.waiter.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'span.login-btn__caption')))
        sleep(1)
        my_logger.logger('info', 'funk -> login > OK')

    def check_login(self):
        """Функция проверки доступа к личному кабинету"""
        my_logger.logger('debug', 'start funk -> check_login')

        try:
            log = self.waiter.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'span.login-btn__caption')))  # Ждём загрузки ярлыка
            loc_log = log.location
            self.driver.execute_script(f'window.scroll({loc_log["x"]}, {loc_log["y"]});')
            sleep(3)

            if log.text.strip().lower() == 'личный кабинет':  # Если текст на ярлыке - 'личный кабинет'
                login_refresh_button = self.waiter.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'button.btn.btn--yellow.login-btn')))
                login_refresh_button.click()  # Нажимаем кнопку на ярлыке

                enter_as_refresh = self.waiter.until(
                    EC.visibility_of_all_elements_located(
                        (By.CSS_SELECTOR, 'a.lk-menu-item.ng-star-inserted:nth-of-type(1)')))
                enter_as_refresh[0].click()  # В выпадающем списке кликаем поле 'поставщик'
            my_logger.logger('info', 'funk -> check_login > OK')

        except Exception as exc:
            my_logger.logger('warning', f'Exception -> funk -> check_login > {exc.__class__}')
            self.check_login()  # В случае ошибки вызывает себя рекурсивно

    def set_only_eat_filter(self):
        """Включает флаг - 'Показывать только закупки на ЕАТ'"""
        my_logger.logger('debug', 'start funk -> set_only_eat_filter')

        try:
            only_eat_switch: WebElement = self.waiter.until(EC.element_to_be_clickable((
                 By.CSS_SELECTOR, 'span.ui-inputswitch-slider')))

            self.driver.execute_script(f'window.scroll({only_eat_switch.location["x"]}, '
                                       f'{only_eat_switch.location["y"]-150})')
            only_eat_switch.click()

        except Exception as exc:
            my_logger.logger('warning', f'funk -> set_only_eat_filter -> Exception -> {exc.__class__} -> restart')
            raise TimeoutException()
        else:
            my_logger.logger('info', 'funk -> set_only_eat_filter -> OK')

    def set_number_filter(self):
        """Записывает номер закупки в поле фильтра"""
        my_logger.logger('debug', 'start funk -> set_number_filter')

        if self.purchase_number:
            keyword_input = self.waiter.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'input#filterField-3-input')))
            self.actions.move_to_element(keyword_input).perform()
            keyword_input.send_keys(self.purchase_number)
        my_logger.logger('info', 'funk -> set_number_filter -> OK')

    def set_keyword_filter(self):
        """Записывает 'Наименование ТРУ' в поле фильтра"""
        my_logger.logger('debug', 'start funk -> set_keyword_filter')

        keyword_input = self.waiter.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'input#filterField-2-input')))
        self.actions.move_to_element(keyword_input).perform()
        keyword_input.send_keys(self.keyword)
        my_logger.logger('info', 'funk -> set_keyword_filter -> OK')

    def set_tin_filter(self):
        """Записывает ИНН в поле фильтра"""
        my_logger.logger('debug', 'start funk -> set_tin_filter')
        tin_input = self.waiter.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, 'input#filterField-14-autocomplete')))
        loc_tin = tin_input.location
        self.driver.execute_script(f'window.scroll({loc_tin["x"]}, {loc_tin["y"]+50});')
        tin_input.send_keys(self.tin)
        my_logger.logger('info', 'funk -> set_tin_filter -> OK')


    def apply_filters(self):
        """Нажимает кнопку 'показать' - применяем введенные значения фильтров"""
        my_logger.logger('debug', 'start funk -> apply_filters')
        apply_filters_button = self.waiter.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'button#applyFilterButton')))
        self.actions.move_to_element(apply_filters_button).click(on_element=apply_filters_button).perform()
        my_logger.logger('info', 'funk -> apply_filters -> OK')

    def get_cards(self):
        """Находит все карточки лотов на странице"""
        my_logger.logger('debug', 'start funk -> get_cards')

        all_cards = self.cards_waiter.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'app-purchase-card.ng-star-inserted')))

        for card in all_cards:
            """Находит номер заказа каждой карточки и записывает его в базу данных"""
            bet_id = card.find_element(By.CSS_SELECTOR, 'h3#tradeNumber')
            Controller.add_bet(bet_id=int(bet_id.text))

        my_logger.logger('info', 'funk -> get_cards -> OK')


    def goto_place_button(self, only_move: bool = False):
        """Нажимает кнопку подать предложение, если не нашёл или кнопка не кликабельна -> повторяет"""
        my_logger.logger('debug', 'start funk -> goto_place_button')

        button_selector = '.c-btn-group > button.c-btn.c-btn--primary'

        if only_move:
            send_bet_button: WebElement = self.waiter.until(EC.visibility_of_element_located(
                (By.CSS_SELECTOR, button_selector)))
            self.actions.move_to_element(send_bet_button).perform()

            my_logger.logger('info', 'funk -> goto_place_button -> only move -> OK')
            return

        while True:
            try:
                place_bet_button: WebElement = self.waiter.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, button_selector)))

                loc_button = place_bet_button.location
                self.driver.execute_script(f'window.scroll({loc_button["x"]}, {loc_button["y"]})')

                place_bet_button.click()

            except Exception as exc:
                my_logger.logger('warning', f'funk -> goto_place_button -> Exception -> {exc.__class__}')
                continue
            else:
                my_logger.logger('info', 'funk -> goto_place_button -> OK')
                break

    def choice_nds(self):
        """Выбирает - ндс - 'не облагается' в шапке документа во время заполнения карточки"""
        my_logger.logger('debug', 'start funk -> choice_nds')

        chc_nds = self.waiter.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR,
                 '#ui-accordiontab-2-content > div > div > app-specification > app-specification-list-general'
                 '-form > div > div.isTaxForAll.flex.tax-switch > div.no-padding.tax-dropdown-2 > '
                 'app-general-tax-dropdown')))
        y_offset = - 150
        while True:
            try:
                chc_nds.click()
                no_tax = chc_nds.find_element(
                    By.CSS_SELECTOR, '.ui-dropdown-items-wrapper p-dropdownitem:nth-of-type(1)')
                no_tax.click()

            except Exception as exc:
                my_logger.logger('warning', f'funk -> choice_nds -> Exception -> {exc.__class__}')

                loc = chc_nds.location
                self.driver.execute_script(f'window.scroll({loc["x"]}, {loc["y"] + y_offset});')
                y_offset -= 50
            else:
                my_logger.logger('info', f'funk -> choice_nds -> "НДС не облагается" -> OK')
                break
            # Устаревшая логика, заменена флагами и выбором на сайте
            # """Циклом во всех позициях устанавливает значение 'Не облагается'"""
            # tax_percent_dropdowns = self.waiter.until(
            #     EC.visibility_of_all_elements_located((By.CSS_SELECTOR, 'p-dropdown[formcontrolname="taxPercent"]')))
            # for dropdown in tax_percent_dropdowns:
            #     y_offset = -10
            #     while True:
            #         try:
            #             dropdown.click()
            #         except ElementClickInterceptedException:
            #             self.driver.execute_script(f'window.scroll(0, {y_offset});')
            #             y_offset -= 10
            #         else:
            #             break
            #     no_tax_item = dropdown.find_element(
            #         By.CSS_SELECTOR, '.ui-dropdown-items-wrapper p-dropdownitem:nth-of-type(1)')
            #     no_tax_item.click()

        """Включает флаг - 'задать НДС для всех' в шапке документа во время заполнения карточки"""
        while True:
            try:
                nds_all: WebElement = self.waiter.until(EC.element_to_be_clickable((
                        By.CSS_SELECTOR, '#tax-for-all-toggler > div > span.ui-inputswitch-slider')))
                nds_all.click()
                sleep(0.5)
                nds_all_control = self.waiter.until(EC.presence_of_element_located(
                        (By.CSS_SELECTOR, 'input#tax-for-all-toggler[type = "checkbox"][aria-labelledby = "label"]')))\
                    .get_dom_attribute('aria-checked')

            except Exception as exc: #(ElementClickInterceptedException, InvalidSelectorException, TimeoutException):
                my_logger.logger('warning', f'funk -> choice_nds -> Exception -> {exc.__class__}')
                continue
            else:
                if nds_all_control == 'true':
                    my_logger.logger('info', 'funk -> choice_nds -> "задать НДС для всех" -> OK')
                    break
            # Устаревшая логика, заменена флагами и выбором на сайте
            # """Циклом во всех позициях ставим флаг 'Цена с НДС'"""
            # is_price_with_tax_checkboxes = self.waiter.until(
            #     EC.visibility_of_all_elements_located((By.CSS_SELECTOR, 'p-checkbox[formcontrolname="isPriceWithTax"]')))
            # for checkbox in is_price_with_tax_checkboxes:
            #     y_offset = -10
            #     while True:
            #         try:
            #             self.waiter.until(EC.element_to_be_clickable(checkbox))
            #             checkbox.click()
            #         except ElementClickInterceptedException:
            #             self.driver.execute_script(f'window.scroll(0, {y_offset});')
            #             y_offset -= 10
            #         else:
            #             break

    def write_descriptions(self):
        """Записывает значения first_desc и second_desc в поля карточки во время заполнения карточки"""
        #TODO Функция иногда зависает -> разобраться думаю проблема в скроле
        my_logger.logger('debug', 'start funk -> write_descriptions')

        select_tru_buttons = self.waiter.until(
            EC.visibility_of_all_elements_located((By.CSS_SELECTOR, 'svg-icon.select-tru__icon.ng-star-inserted')))
        for select_tru_button in select_tru_buttons:
            y_offset = -10
            while True:
                try:
                    # print(select_tru_button.text)  # пусто, текста нет
                    select_tru_button.click()
                except ElementClickInterceptedException:
                    self.driver.execute_script(f'window.scroll(0, {y_offset});')
                    y_offset -= 10
                else:
                    break
            create_new_button = self.waiter.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, '.tru-description-modal__action:nth-of-type(3)')))
            create_new_button.click()
            tru_name_input = self.waiter.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[formcontrolname="offerName"]')))
            tru_name_input.send_keys(self.first_desc)
            tru_desc_input = self.waiter.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'textarea[formcontrolname="offerDescription"]')))
            tru_desc_input.send_keys(self.second_desc)
            accept_tru_button = self.waiter.until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, '.modal-window__buttons-container > button:nth-of-type(2)')))
            accept_tru_button.click()
        my_logger.logger('info', 'funk -> write_descriptions -> OK')

    def card_editing_pencil(self):
        """Находим элемент возможности редактирования карточки 'карандаш'"""
        my_logger.logger('debug', 'start funk -> card_editing_pencil')

        try:
            self.error_waiter.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'svg-icon.select-tru__icon.ng-star-inserted')))
        except TimeoutException:
            print(f'{Fore.RED}Ошибка! '
                  f'{Fore.MAGENTA}В этом лоте нет маркера возможности редактирования полей ТРУ{Fore.RESET}')
        else:
            my_logger.logger('info', 'funk -> card_editing_pencil -> OK')
            self.write_descriptions()

    def price_inputs(self):
        """Циклом во всех позициях меняем стоимость на 0,01"""
        my_logger.logger('debug', 'start funk -> price_inputs')

        price_inputs = self.waiter.until(EC.visibility_of_all_elements_located(
            (By.CSS_SELECTOR, 'td.col-price.col-editable > input')))
        for price_input in price_inputs:
            y_offset = 10
            up = True
            while True:
                try:
                    price_input.send_keys(Keys.BACKSPACE * 20)
                    price_input.send_keys(Keys.DELETE * 20)
                    price_input.send_keys('0,01')
                except ElementClickInterceptedException:
                    self.driver.execute_script(f'window.scroll(0, {y_offset});')
                    if y_offset < 500 and up:
                        y_offset += 10
                    else:
                        up = False
                        y_offset -= 10
                else:
                    my_logger.logger('info', 'funk -> price_inputs -> OK')
                    break

    def place_confirm_button(self):
        """Находит и нажимает кнопку подтвердить во всплывающем окне"""
        my_logger.logger('debug', 'start funk -> place_confirm_button')

        confirm_bet_button = self.waiter.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR,
                 '.dynamic-modal-window__buttons-container > button.c-btn.c-btn--secondary:nth-of-type(2)')))
        confirm_bet_button.click()
        my_logger.logger('info', 'funk -> place_confirm_button -> OK')

    def place_sign_in_button(self):
        """Находит и нажимает кнопку 'подписать' во всплывающем окне"""
        my_logger.logger('debug', 'start funk -> place_sign_in_button')

        sign_in_button = self.waiter.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'button#signButton')))
        sign_in_button.click()
        my_logger.logger('info', 'funk -> place_sign_in_button -> OK')

    def access_confirmation(self):
        """Блок подтверждения доступа"""
        my_logger.logger('debug', 'start funk -> access_confirmation')

        try:
            app = Application(backend="uia").connect(title="Подтверждение доступа", timeout=5)
            confirmWin = app.window(title_re=u'Подтверждение доступа')
            if confirmWin.exists(timeout=10, retry_interval=1):
                confirmWin.set_focus()
                yesBtn = confirmWin[u'&Да']
                yesBtn.click()
        except Exception as exc:
            my_logger.logger('warning', f'Exception -> funk access_confirmation -> step #1 -> {exc.__class__}')
            sleep(2)
            try:
                app = Application(backend="uia").connect(title="Подтверждение доступа", timeout=5)
                confirmWin = app.window(title_re=u'Подтверждение доступа')
                if confirmWin.exists(timeout=10, retry_interval=1):
                    confirmWin.set_focus()
                    yesBtn = confirmWin[u'&Да']
                    yesBtn.click()
            except Exception as exc:
                my_logger.logger('warning', f'Exception -> funk access_confirmation -> step #2 -> {exc.__class__}')
                return False
        my_logger.logger('info', 'funk -> access_confirmation -> OK')

    def checker_lot(self):
        """Перепроверка лота на соответствие ИНН и наименованию организации, если указаны"""
        print(f'{Fore.MAGENTA}Перепроверка лота:', Fore.RESET, end=' ')
        if self.tin:
            inn_in_lot: WebElement = self.waiter.until(
                 EC.visibility_of_element_located(
                     (By.XPATH,
                      '/html/body/app-root/div/main/app-purchase-application/form/div[2]/div/app-accordion-section[1]/div/p-accordion/div/p-accordiontab/div[2]/div/div/app-customer-info/div[2]/div[2]')))

            if inn_in_lot.text == self.tin:
                print(Fore.GREEN, 'ИНН совпадает.', Fore.RESET, end=' ')
            else:
                print(Fore.RED, 'ИНН не совпадает -> сброс заполнения.', Fore.RESET)
                return False
        else:
            print(Fore.YELLOW, 'ИНН не указан.', Fore.RESET, end=' ')

        if self.name_org_client:
            name_org: WebElement = self.waiter.until(
                EC.visibility_of_element_located(
                    (By.XPATH, '/html/body/app-root/div/main/app-purchase-application/form/div[2]/div/app-accordion-section[1]/div/p-accordion/div/p-accordiontab/div[2]/div/div/app-customer-info/div[1]/div[2]/app-general-link/a')))
            if name_org.text.lower() == self.name_org_client.lower():
                print(Fore.GREEN, 'Наименование организации совпадает.', Fore.RESET)
            else:
                print(Fore.RED, 'Наименование организации не совпадает -> сброс заполнения.', Fore.RESET)
                return False
        else:
            print(Fore.YELLOW, 'Наименование организации не указано.', Fore.RESET)

        print(f'{Fore.MAGENTA}Успешно: {Fore.GREEN}перехожу к заполнению лота', Fore.RESET)
        return True

    def place_bet(self):
        my_logger.logger('debug', 'start funk -> place_bet')
        self.goto_place_button(only_move=True)  # Находит и скролит к кнопке - 'подать предложение'

        # Перепроверка лота
        if self.tin or self.name_org_client:
            if not self.checker_lot():
                return False

        self.choice_nds()  # Установки НДС
        self.card_editing_pencil()  # редактирование карточки 'карандаш'
        self.price_inputs()  # во всех позициях меняем стоимость на 0,01
        self.goto_place_button()  # Находит и нажимает на кнопку - 'подать предложение'
        self.place_confirm_button()  # Находит и нажимает кнопку - 'подтвердить'
        self.place_sign_in_button()  # Находит и нажимает кнопку 'подписать'
        self.access_confirmation()  # Подтверждение доступа

        # изначальное значение
        # certificates: List[WebElement] = self.waiter.until(
        #     EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'span.fullname')))

        certificates: List[WebElement] = self.waiter.until(
            EC.presence_of_all_elements_located((
                By.XPATH, "/html/body/p-dynamicdialog/div/div/div/app-certicate-select-modal/section/app-certificates-list/ul/li/label/p/span[@class='fullname']")))

        print('Список доступных сертификатов:')
        for certificate in certificates:
            print(certificate.text)

        for certificate in certificates:
            if self.certificate_name.strip().lower() == certificate.text.strip().lower():
                print('\nВыбран сертификат:', certificate.text)
                certificate.click()
                break

        sign_in_button = self.waiter.until(EC.visibility_of_element_located((
            By.CSS_SELECTOR, '.modal-wrapper__btns > button.c-btn.c-btn--primary')))

        if self.automatic_sbsc.lower() == 'y':
            sign_in_button.click()  # остановились тут


        my_logger.logger('warning', 'ДАЛЬШЕ НЕПРОВЕРЕННАЯ ЛОГИКА')

        # Блок выбора ключевого носителя
        try:
            my_logger.logger('debug', 'Выбор ключевого носителя шаг 1')

            app = Application(backend="uia").connect(title_re="Выбор ключевого носителя - КриптоПро CSP", timeout=5)
            confirmWin = app.window(title_re=u'Выбор ключевого носителя - КриптоПро CSP')
            if confirmWin.exists(timeout=10, retry_interval=1):
                confirmWin.set_focus()
                yesBtn = confirmWin[u'ОК']
                yesBtn.click()
        except Exception as exc:
            my_logger.logger('warning', f'ошибка при выборе ключевого носителя на шаге 1: {exc.__class__}')
            sleep(2)
            try:
                my_logger.logger('debug', 'Выбор ключевого носителя шаг 2')

                app = Application(backend="uia").connect(title_re="Выбор ключевого носителя - КриптоПро CSP", timeout=5)
                confirmWin = app.window(title_re=u'Выбор ключевого носителя - КриптоПро CSP')
                if confirmWin.exists(timeout=10, retry_interval=1):
                    confirmWin.set_focus()
                    yesBtn = confirmWin[u'ОК']
                    yesBtn.click()
            except Exception as exc:
                my_logger.logger('warning', f'ошибка при выборе ключевого носителя на шаге 1: {exc.__class__}')

                return False

        #Блок автоматической подписи лота
        if self.automatic_sbsc.lower() == 'y':
            try:
                my_logger.logger('debug', 'Блок автоматической подписи лота')
                # css_selector: #modal > div > button
                # x_path: //*[@id="modal"]/div/button
                # full_x_path: /html/body/p-dynamicdialog/div/div/div/app-certicate-select-modal/section/div/button
                subscribe = self.waiter.until(EC.element_to_be_clickable((
                        By.XPATH, '/html/body/p-dynamicdialog/div/div/div/app-certicate-select-modal/section/div/button')))
                subscribe.click()
            except TimeoutException:
                my_logger.logger('warning', 'TimeoutException или не находит кнопку')
            except ElementClickInterceptedException:
                my_logger.logger('warning', 'ElementClickInterceptedException - кнопка не кликабельная')
            else:
                input('Лот успешно подписан, для завершения работы нажмите Enter: ')

        return True

    def work(self):
        my_logger.logger('debug', 'start funk -> work')

        self.check_login()

        try:
            self.get_cards()
        except TimeoutException:
            return False

        """Находит все карточки лотов на странице"""
        all_cards = self.waiter.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'app-purchase-card.ng-star-inserted')))
        for card in all_cards:
            bet_id = card.find_element(By.CSS_SELECTOR, 'h3#tradeNumber') # Находит номер закупки в карточке лота

            # Если номера закупки нет в базе данных и среди исключений введённых пользователем
            if not Controller.get_bet_status(int(bet_id.text)) and int(bet_id.text) not in self.bets_to_exclude:
                send_bet_button = card.find_element(By.CSS_SELECTOR, 'button#applicationSendButton')  # Находит
                send_bet_button.click()  # И кликает кнопку 'подать предложение'

                # Если предложение успешно подано(в том числе подписано ЭЦП)
                if self.place_bet():
                    Controller.update_bet_status(True, bet_id=int(bet_id.text))  # Записывает его номер в БД
                    my_logger.logger('info', 'funk -> work -> OK')
                    return True
                else:
                    return False

    def make_bet(self):

        while True:
            my_logger.logger('debug', 'start funk -> make_bet')
            self.driver.get(TRADES_URL)

            try:
                my_logger.logger('debug', 'start bloc -> set filter')
                if self.only_EAT:
                    self.set_only_eat_filter()  # Включаем флаг EAT
                if self.keyword:
                    self.set_keyword_filter()  # Запись ТРУ в поле фильтра "ключевая фраза"
                if self.tin:
                    self.set_tin_filter()  # Запись ИНН в поле фильтра
                if self.purchase_number:
                    self.set_number_filter()  # Запись номера закупки в поле фильтра
                self.apply_filters()  # Применить фильтр
                my_logger.logger('info', 'bloc -> set filter -> OK')
            except Exception as exc:
                my_logger.logger('warning', f'Exception -> bloc set filter: {exc.__class__} -> restart')
                sleep(1)
                continue

            try:
                self.work()
                my_logger.logger('info', 'funk -> make_bet -> OK')
            except Exception as exc:
                my_logger.logger('warning', f'Exception -> func work: {exc.__class__} -> restart')
                sleep(1)
                continue
