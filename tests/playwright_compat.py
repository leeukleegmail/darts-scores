import time
from typing import Any, Callable


class By:
    ID = "id"
    NAME = "name"
    CSS_SELECTOR = "css selector"
    XPATH = "xpath"
    TAG_NAME = "tag name"


class Keys:
    COMMAND = "Meta"
    DELETE = "Delete"


class NoSuchElementException(Exception):
    pass


class StaleElementReferenceException(Exception):
    pass


def _selector(by: str, value: str) -> str:
    if by == By.ID:
        return f"#{value}"
    if by == By.TAG_NAME:
        return value
    if by == By.NAME:
        return f"[name='{value}']"
    if by in (By.CSS_SELECTOR, By.XPATH):
        return f"xpath={value}" if by == By.XPATH else value
    raise ValueError(f"Unsupported selector strategy: {by}")


class Element:
    def __init__(self, locator, selector: str):
        self.locator = locator
        self.selector = selector
        self._select_all = False

    @property
    def text(self) -> str:
        return self.locator.inner_text()

    def find_element(self, by: str, value: str):
        selector = _selector(by, value)
        return Element(self.locator.locator(selector).first, f"{self.selector} >> {selector}")

    def find_elements(self, by: str, value: str):
        selector = _selector(by, value)
        return [
            Element(item, f"{self.selector} >> {selector}")
            for item in self.locator.locator(selector).all()
        ]

    def click(self):
        self.locator.click()

    def clear(self):
        self.locator.fill("")

    def send_keys(self, *values):
        for value in values:
            if value == Keys.COMMAND:
                self._select_all = True
            elif value == Keys.DELETE:
                if self._select_all:
                    self.locator.fill("")
                    self.locator.dispatch_event("change")
                    self._select_all = False
                else:
                    self.locator.press("Delete")
            else:
                if len(value) > 1 and value in {"Enter", "Tab"}:
                    self.locator.press(value)
                else:
                    self.locator.fill(self.locator.input_value() + str(value))
                    self.locator.dispatch_event("change")

    def get_attribute(self, name: str):
        if name == "value":
            tag_name = self.locator.evaluate("(element) => element.tagName")
            if tag_name in {"INPUT", "TEXTAREA", "SELECT"}:
                return self.locator.input_value()
        value = self.locator.get_attribute(name)
        if name in {"disabled", "readonly", "checked"} and value == "":
            return "true"
        return value

    def is_displayed(self) -> bool:
        return self.locator.is_visible(timeout=500)

    def is_enabled(self) -> bool:
        return self.locator.is_enabled(timeout=500)

    def is_selected(self) -> bool:
        return self.locator.is_checked(timeout=500)


class Dialog:
    def __init__(self, dialog):
        self.dialog = dialog
        self.text = dialog.message

    def dismiss(self):
        try:
            self.dialog.dismiss()
        except Exception:
            pass


class PageAdapter:
    def __init__(self, page):
        self.page = page
        self.last_dialog = None

        def handle_dialog(dialog):
            self.last_dialog = Dialog(dialog)
            dialog.dismiss()

        page.on("dialog", handle_dialog)

    def get(self, url: str):
        self.page.goto(url)

    def find_element(self, by: str, value: str):
        selector = _selector(by, value)
        locator = self.page.locator(selector).first
        if locator.count() == 0:
            raise NoSuchElementException(value)
        return Element(locator, selector)

    def find_elements(self, by: str, value: str):
        selector = _selector(by, value)
        return [Element(item, selector) for item in self.page.locator(selector).all()]

    def execute_script(self, script: str, *args):
        arguments = [
            (
                {"selector": arg.locator.evaluate(
                    """(element) => {
                        const id = `playwright-script-${crypto.randomUUID()}`;
                        element.setAttribute('data-playwright-script-id', id);
                        return `[data-playwright-script-id="${id}"]`;
                    }"""
                )}
                if isinstance(arg, Element)
                else {"value": arg}
            )
            for arg in args
        ]
        return self.page.evaluate(
            """({script, arguments}) => {
                const resolve = (selector) => {
                    if (!selector) return selector;
                    if (selector.startsWith('//') || selector.startsWith('(//')) {
                        return document.evaluate(
                            selector, document, null,
                            XPathResult.FIRST_ORDERED_NODE_TYPE, null
                        ).singleNodeValue;
                    }
                    return document.querySelector(selector);
                };
                const resolved = arguments.map(({selector, value}) =>
                    selector ? resolve(selector) : value
                );
                return (function () { %s }).apply(null, resolved);
            }""" % script,
            {"script": script, "arguments": arguments},
        )


class WebDriverWait:
    def __init__(self, browser, timeout: float):
        self.browser = browser
        self.timeout = timeout

    def until(self, condition: Callable[[PageAdapter], Any]):
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            try:
                result = condition(self.browser)
                if result:
                    return result
            except Exception:
                pass
            time.sleep(0.05)
        raise AssertionError("Timed out waiting for condition")

    def until_not(self, condition):
        return self.until(lambda browser: not condition(browser))


class _ExpectedConditions:
    def _element(self, locator):
        by, value = locator
        return lambda browser: browser.find_element(by, value)

    def presence_of_element_located(self, locator):
        return self._element(locator)

    def visibility_of_element_located(self, locator):
        return lambda browser: (
            element if (element := self._element(locator)(browser)).is_displayed() else False
        )

    def element_to_be_clickable(self, locator):
        return lambda browser: (
            element
            if (element := self._element(locator)(browser)).is_displayed() and element.is_enabled()
            else False
        )

    def invisibility_of_element_located(self, locator):
        return lambda browser: (
            not browser.find_element(*locator).is_displayed()
        )

    def presence_of_all_elements_located(self, locator):
        return lambda browser: (
            elements if (elements := browser.find_elements(*locator)) else False
        )

    def text_to_be_present_in_element(self, locator, text):
        return lambda browser: text in browser.find_element(*locator).text

    def alert_is_present(self):
        return lambda browser: browser.last_dialog

    def staleness_of(self, element):
        return lambda browser: True


ec = _ExpectedConditions()


class Select:
    def __init__(self, element: Element):
        self.element = element

    @property
    def first_selected_option(self):
        value = self.element.locator.input_value()
        return Element(
            self.element.locator.locator(f"option[value='{value}']").first,
            f"{self.element.selector} option[value='{value}']",
        )

    def select_by_value(self, value: str):
        self.element.locator.select_option(value=value)

    @property
    def options(self):
        return [
            Element(option, f"{self.element.selector} option")
            for option in self.element.locator.locator("option").all()
        ]
