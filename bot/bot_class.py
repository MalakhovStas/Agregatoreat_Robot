from time import sleep

from pywinauto.application import Application
from selenium.common.exceptions import StaleElementReferenceException, ElementClickInterceptedException, \
    TimeoutException, NoSuchElementException
from selenium.webdriver import Chrome, ActionChains, Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.remote.webelement import WebElement
from loguru import logger

from config import MAIN_URL, TRADES_URL, LOGIN_URL

from database import Controller
from colorama import init, Fore


LOG_FMT = '{time:DD-MM-YYYY at HH:mm:ss} | {level: <8} | func: {function: ^15} | line: {line: >3} | message: {message}'
logger.add(sink='logs/debug.log', format=LOG_FMT, level='WARNING', diagnose=True, backtrace=False,
           rotation="100 MB", retention=1, compression="zip")


class Bot:
    def __init__(self, mail: str, password: str, certificate_name: str, tin: str, keyword: str, first_desc: str,
                 second_desc: str, bets_to_exclude: str, purchase_number: str, only_EAT: str, automatic_sbsc: str,
                 wait_time: int = 20, error_time: int = 1, cards_time: int = 3):
        self.service = Service(executable_path=ChromeDriverManager().install())
        self.options = Options()
        self.options.add_argument('--log-level=3')
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
        self.keyword = keyword.strip()
        self.first_desc = first_desc.strip()
        self.second_desc = second_desc.strip()
        self.bets_to_exclude: list = [int(bet_to_exclude) for bet_to_exclude in
                                      bets_to_exclude.split() if len(bet_to_exclude) and bet_to_exclude.isdigit()]
        self. purchase_number = purchase_number.strip()
        self.only_EAT = int(only_EAT.strip()) if only_EAT.strip().isdigit() else 0
        self.automatic_sbsc = automatic_sbsc

    def login(self):
        self.driver.get(LOGIN_URL)
        login_input = self.waiter.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[name="Username"]')))
        login_input.send_keys(self.mail)

        password_input = self.waiter.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[name="Password"]')))
        password_input.send_keys(self.password)

        #старый клик на кнопку входа в лк
        login_button = self.waiter.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'button[value="login"]')))
        # login_button = self.waiter.until(
        #     EC.visibility_of_element_located((By.CSS_SELECTOR, '#loginForm > fieldset > button')))
        login_button.click()

        self.waiter.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'span.login-btn__caption')))
        logger.debug('Вход в личный кабинет')
        sleep(2)

    def check_login(self):
        """Функция проверки доступа к личному кабинету"""
        try:
            logger.debug('Проверка доступа к личному кабинету')
            log = self.waiter.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'span.login-btn__caption')))  # Ждём загрузки ярлыка
            if log.text.strip().lower() == 'личный кабинет':  # Если текст на ярлыке - 'личный кабинет'
                login_refresh_button = self.waiter.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'button.btn.btn--yellow.login-btn')))
                login_refresh_button.click()  # Нажимаем кнопку на ярлыке
                enter_as_refresh = self.waiter.until(
                    EC.visibility_of_all_elements_located(
                        (By.CSS_SELECTOR, 'a.lk-menu-item.ng-star-inserted:nth-of-type(1)')))
                enter_as_refresh[0].click()  # В выпадающем списке кликаем поле 'поставщик'
        except Exception:
            logger.warning('Ошибка -> ещё попытка')
            self.check_login()  # В случае ошибки вызывает себя рекурсивно

    def set_only_eat_filter(self):
        """Включает флаг - 'Показывать только закупки на ЕАТ'"""
        logger.debug('Вкл флаг - Показывать только закупки на ЕАТ')
        only_eat_switch = self.waiter.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'span.ui-inputswitch-slider')))
        self.actions.move_to_element(only_eat_switch).click(on_element=only_eat_switch).perform()

    def set_number_filter(self):
        """Записывает номер закупки в поле фильтра"""
        if self.purchase_number:
            logger.debug('Записываю номер лота в поле фильтра')
            keyword_input = self.waiter.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'input#filterField-3-input')))
            self.actions.move_to_element(keyword_input).perform()
            keyword_input.send_keys(self.purchase_number)

    def set_keyword_filter(self):
        """Записывает 'Наименование ТРУ' в поле фильтра"""
        logger.debug('Записываю "Наименование ТРУ" в поле фильтра')
        keyword_input = self.waiter.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'input#filterField-2-input')))
        self.actions.move_to_element(keyword_input).perform()
        keyword_input.send_keys(self.keyword)

    def set_tin_filter(self):
        """Записывает ИНН в поле фильтра"""
        logger.debug('Записываю ИНН в поле фильтра')
        tin_input = self.waiter.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'input#filterField-14-autocomplete')))
        self.actions.move_to_element(tin_input).perform()
        tin_input.send_keys(self.tin)

    def apply_filters(self):
        """Нажимает кнопку 'показать' - применяем введенные значения фильтров"""
        logger.debug('Применяю фильтр')
        apply_filters_button = self.waiter.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'button#applyFilterButton')))
        self.actions.move_to_element(apply_filters_button).click(on_element=apply_filters_button).perform()

    def get_cards(self):
        """Находит все лоты на странице"""
        logger.debug('Поиск всех лотов на странице')
        while True:
            try:
                sleep(0.5)
                all_cards = self.cards_waiter.until(
                    EC.presence_of_all_elements_located((
                        By.CSS_SELECTOR, 'app-purchase-card.ng-star-inserted')))
                logger.debug(f'Ок - найдено лотов на странице: {len(all_cards)}')
                for card in all_cards:
                    """Находит номер каждого лота и записывает его в базу данных"""
                    bet_id = card.find_element(By.CSS_SELECTOR, 'h3#tradeNumber')
                    Controller.add_bet(bet_id=int(bet_id.text))

            except StaleElementReferenceException:
                logger.warning(f'Лоты на странице не найдены, ещё попытка')

            else:
                return all_cards
                # break

    def goto_place_button(self):
        """Нажимает кнопку подать предложение, если не нашёл кнопку -> скролит вверх"""
        y_offset = 10
        while True:
            try:
                logger.debug('Поиск кнопки -> "Подать предложение"')
                place_bet_button: WebElement = self.waiter.until(EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, '.c-btn-group > button.c-btn.c-btn--primary')))
                self.driver.execute_script(
                    f'window.scroll({place_bet_button.location["x"]}, {place_bet_button.location["y"]} + {y_offset})')
                sleep(0.5)

                place_bet_button.click()

            except ElementClickInterceptedException:
                logger.warning(f'Ошибка -> кнопка "Подать предложение" -> не кликабельна, ещё попытка')
                self.driver.execute_script(f'window.scroll(0, {y_offset})')
                y_offset += 10

            except NoSuchElementException:
                logger.warning(f'Ошибка -> кнопка "Подать предложение" -> на странице не найдена, ещё попытка')
                self.driver.execute_script(f'window.scroll(0, {y_offset})')
                y_offset += 10

            else:
                logger.debug('Ок -> "Подать предложение"')
                break

    # TODO проверить работу этого метода
    def choice_nds(self):
        """Выбирает - ндс - 'не облагается' в шапке документа во время заполнения карточки"""

        y_offset = -150
        while True:
            try:
                logger.debug('Поиск элемента для выбора ставки НДС')
                chc_nds: WebElement = self.waiter.until(EC.visibility_of_element_located((
                        By.CSS_SELECTOR, '#ui-accordiontab-2-content > div > div > app-specification > app-specification-list-general-form > div > div.isTaxForAll.flex.tax-switch > div.no-padding.tax-dropdown-2 > app-general-tax-dropdown')))
                self.driver.execute_script(
                    f'window.scroll({chc_nds.location["x"]}, {chc_nds.location["y"] + y_offset});')
                sleep(0.5)

                chc_nds.click()

            except ElementClickInterceptedException:
                logger.warning('Ошибка -> элемент не кликабельный, ещё попытка')
                y_offset -= 10

            except NoSuchElementException:
                logger.warning('Ошибка -> элемент на странице не найден, ещё попытка')
                y_offset -= 10

            except Exception as exc:
                print(exc.__class__)

            else:
                logger.debug('ОК -> открыт выпадающий список')
                while True:
                    try:
                        logger.debug('Поиск элемента -> НДС "Hе облагается"')
                        sleep(0.5)
                        no_tax = chc_nds.find_element(
                            By.CSS_SELECTOR, '.ui-dropdown-items-wrapper p-dropdownitem:nth-of-type(1)')
                        if no_tax.text == 'Не облагается':
                            no_tax.click()
                            break
                    except Exception as exc:
                        logger.warning(f'Ошибка выбора - НДС "не облагается": {exc.__class__}, ещё попытка')

                sleep(0.5)
                if chc_nds.text == "Не облагается":
                    logger.debug('Ок -> выбрано -> НДС "не облагается"')
                    break

        """Включает флаг - 'задать НДС для всех' в шапке документа во время заполнения карточки"""
        while True:
            try:
                logger.debug('Включаю - "задать НДС для всех"')
                nds_all = self.waiter.until(
                    EC.element_to_be_clickable((
                        By.CSS_SELECTOR, '#tax-for-all-toggler > div > span.ui-inputswitch-slider')))
                nds_all.click()
                sleep(0.5)
                nds_all_control = self.waiter.until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, 'input#tax-for-all-toggler[type = "checkbox"][aria-labelledby = "label"]'))) \
                    .get_dom_attribute('aria-checked')
            except (ElementClickInterceptedException, TimeoutException):
                logger.warning('Ошибка включения флага - "задать НДС для всех", ещё попытка')
                continue
            else:
                if nds_all_control == 'true':
                    logger.debug('Ок -> вкл -> "задать НДС для всех"')
                    break

    def write_descriptions(self):
        """Записывает значения first_desc и second_desc в поля карточки во время заполнения карточки"""
        logger.debug('Во всех позициях записываю значения ТРУ')
        select_tru_buttons = self.waiter.until(
            EC.visibility_of_all_elements_located((By.CSS_SELECTOR, 'svg-icon.select-tru__icon.ng-star-inserted')))
        for select_tru_button in select_tru_buttons:
            y_offset = -30
            while True:
                try:
                    select_tru_button.click()
                except ElementClickInterceptedException:
                    # logger.warning('Ошибка записи значения ТРУ -> элемент не кликабельный, ещё попытка')
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
            logger.debug('ОК записано -> значения ТРУ')

    def place_bet(self):
        """Находит и кликает кнопку - 'подать предложение' """
        # logger.debug('Поиск кнопки -> "Подать предложение"')
        # send_bet_button = self.waiter.until(
        #     EC.visibility_of_element_located(
        #         (By.CSS_SELECTOR, '.c-btn-group > button.c-btn.c-btn--primary')))
        # self.actions.move_to_element(send_bet_button).perform()
        self.goto_place_button()
        """Выбирает - ндс - 'не облагается' в шапке документа во время заполнения карточки"""
        self.choice_nds()
        try:
            """Находим элемент возможности редактирования полей ТРУ - 'карандаш'"""
            logger.debug('Поиск элемента возможности редактирования полей ТРУ -> "карандаш"')
            self.error_waiter.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'svg-icon.select-tru__icon.ng-star-inserted')))
        except TimeoutException:
            logger.warning('Ошибка -> в этом лоте нет маркера возможности редактирования полей ТРУ -> "карандаш"')
        else:
            """Записывает значения first_desc и second_desc в поля карточки во время заполнения карточки"""
            self.write_descriptions()

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
        """Находит и циклом во всех позициях меняет стоимость на 0,01"""
        price_inputs = self.waiter.until(
            EC.visibility_of_all_elements_located((By.CSS_SELECTOR, 'td.col-price.col-editable > input')))

        logger.debug('Во всех позициях меняем стоимость на 0,01')
        for price_input in price_inputs:
            y_offset = 10
            up = True
            while True:
                try:
                    price_input.send_keys(Keys.BACKSPACE*20)
                    price_input.send_keys(Keys.DELETE*20)
                    price_input.send_keys('0,01')
                except ElementClickInterceptedException:
                    self.driver.execute_script(f'window.scroll(0, {y_offset});')
                    if y_offset < 500 and up:
                        y_offset += 10
                    else:
                        up = False
                        y_offset -= 10
                else:
                    logger.debug('Ок -> изменена стоимость на 0,01')
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
        """Находит и кликает кнопку - 'подать предложение' """
        self.goto_place_button()

        confirm_bet_button = self.waiter.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR,
                 '.dynamic-modal-window__buttons-container > button.c-btn.c-btn--secondary:nth-of-type(2)')))
        confirm_bet_button.click()
        sign_in_button = self.waiter.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'button#signButton')))
        sign_in_button.click()

        try:
            app = Application(backend="uia").connect(title="Подтверждение доступа", timeout=5)
            confirmWin = app.window(title_re=u'Подтверждение доступа')
            if confirmWin.exists(timeout=10, retry_interval=1):
                confirmWin.set_focus()
                yesBtn = confirmWin[u'&Да']
                yesBtn.click()
                logger.debug('ОК -> подтверждение доступа')
        except Exception as e:
            logger.warning('Ошибка -> подтверждения доступа, ещё попытка')
            sleep(2)
            try:
                app = Application(backend="uia").connect(title="Подтверждение доступа", timeout=5)
                confirmWin = app.window(title_re=u'Подтверждение доступа')
                if confirmWin.exists(timeout=10, retry_interval=1):
                    confirmWin.set_focus()
                    yesBtn = confirmWin[u'&Да']
                    yesBtn.click()
                    logger.debug('ОК -> подтверждение доступа')

            except Exception as e:
                logger.error('Ошибка -> доступ подтвердить не удалось')
                return False

        logger.debug('Поиск списка сертификатов')
        certificates = self.waiter.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'span.fullname')))
        for certificate in certificates:
            if self.certificate_name.strip().lower() == certificate.text.strip().lower():
                certificate.click()
                logger.debug('ОК -> выбор сертификата')
                break

        logger.debug('Поиск кнопки -> "Подписать"')
        sign_in_button = self.waiter.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '.modal-wrapper__btns > button.c-btn.c-btn--primary')))
        sleep(0.5)
        sign_in_button.click()
        logger.debug('ОК -> "Подписать"')

        try:
            app = Application(backend="uia").connect(title_re="Выбор ключевого носителя - КриптоПро CSP", timeout=5)
            confirmWin = app.window(title_re=u'Выбор ключевого носителя - КриптоПро CSP')
            if confirmWin.exists(timeout=10, retry_interval=1):
                confirmWin.set_focus()
                yesBtn = confirmWin[u'ОК']
                yesBtn.click()
                logger.debug('ОК -> Выбор ключевого носителя - КриптоПро CSP')

        except Exception as e:
            logger.warning('Ошибка -> Выбора ключевого носителя - КриптоПро CSP, ещё попытка')
            sleep(2)
            try:
                app = Application(backend="uia").connect(title_re="Выбор ключевого носителя - КриптоПро CSP", timeout=5)
                confirmWin = app.window(title_re=u'Выбор ключевого носителя - КриптоПро CSP')
                if confirmWin.exists(timeout=10, retry_interval=1):
                    confirmWin.set_focus()
                    yesBtn = confirmWin[u'ОК']
                    yesBtn.click()
                    logger.debug('ОК -> Выбор ключевого носителя - КриптоПро CSP')

            except Exception as e:
                logger.error('Ошибка -> ключевой носитель - КриптоПро CSP -> выбрать не удалось')
                return False

        return True

    def work(self):
        self.check_login()
        try:
            """Находит все карточки лотов на странице"""
            all_cards = self.get_cards()
        except TimeoutException:
            logger.warning(f'Нет лотов удовлетворяющих условиям поиска, ещё попытка')
            return False
        # """Находит все карточки лотов на странице"""
        # all_cards = self.waiter.until(
        #     EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'app-purchase-card.ng-star-inserted')))
        for card in all_cards:
            bet_id = card.find_element(By.CSS_SELECTOR, 'h3#tradeNumber') # Находит номер закупки в карточке лота

            # Если номера закупки нет в базе данных и среди исключений введённых пользователем
            if not Controller.get_bet_status(int(bet_id.text)) and int(bet_id.text) not in self.bets_to_exclude:
                logger.info(f'Подготовка к подписи -> лот # {bet_id.text}')

                send_bet_button = card.find_element(By.CSS_SELECTOR, 'button#applicationSendButton')  # Находит
                send_bet_button.click()  # И кликает кнопку 'подать предложение'

                # Если предложение успешно подано(в том числе подписано ЭЦП)
                if self.place_bet():
                    Controller.update_bet_status(True, bet_id=int(bet_id.text))  # Записывает его номер в БД
                    logger.info(f'Лот # {bet_id.text} -> подписан успешно!')
                    return True
                else:
                    logger.warning(f'Не удалось подписать -> лот # {bet_id.text}')
                    return False

    def make_bet(self):
        while True:
            self.driver.get(TRADES_URL)
            logger.info(f'Настройка фильтра для поиска лотов')

            try:
                if self.only_EAT: self.set_only_eat_filter()  # Включаем флаг EAT
                if self.keyword: self.set_keyword_filter()  # Запись ТРУ в поле фильтра "ключевая фраза"
                if self.tin: self.set_tin_filter()  # Запись ИНН в поле фильтра
                if self.purchase_number: self.set_number_filter()  # Запись номера закупки в поле фильтра
                self.apply_filters()  # Применить фильтр
            except TimeoutException:
                logger.warning(f'Ошибка настройки фильтра -> Timeout, ещё попытка')
                # self.driver.get(TRADES_URL)
                continue
            except Exception as e:
                sleep(2)
                # print(f'Логи по фильтру: {e.__class__}, {e}')
                logger.warning(f'Ошибка настройки фильтра -> {e.__class__}, ещё попытка')
                continue
            try:
                self.work()
            except TimeoutException:
                logger.warning(f'Ошибка основного процесса -> Timeout, ещё попытка')
                continue
            except Exception as e:
                sleep(2)
                # print(f'Логи -> func work: {e.__class__}, {e}')
                logger.warning(f'Ошибка основного процесса -> {e.__class__}, ещё попытка')
                continue
