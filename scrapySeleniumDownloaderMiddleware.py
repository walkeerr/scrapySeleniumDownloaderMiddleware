from twisted.internet import defer
from scrapy import signals
import _thread
from concurrent.futures import ThreadPoolExecutor
from scrapy.http import HtmlResponse
from selenium.webdriver import Chrome
from selenium.webdriver import ChromeOptions



import string
import zipfile
import time

def create_proxyauth_extension(tunnelhost, tunnelport, proxy_username, proxy_password, scheme='http', plugin_path=None):
    if plugin_path is None:
        plugin_path = 'vimm_chrome_proxyauth_plugin.zip'
    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Chrome Proxy",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {
            "scripts": ["background.js"]
        },
        "minimum_chrome_version":"22.0.0"
    }
    """
    background_js = string.Template(
        """
        var config = {
                mode: "fixed_servers",
                rules: {
                singleProxy: {
                    scheme: "${scheme}",
                    host: "${host}",
                    port: parseInt(${port})
                },
                bypassList: ["foobar.com"]
                }
            };

        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

        function callbackFn(details) {
            return {
                authCredentials: {
                    username: "${username}",
                    password: "${password}"
                }
            };
        }

        chrome.webRequest.onAuthRequired.addListener(
                    callbackFn,
                    {urls: ["<all_urls>"]},
                    ['blocking']
        );
        """
    ).substitute(
        host=tunnelhost,
        port=tunnelport,
        username=proxy_username,
        password=proxy_password,
        scheme=scheme,
    )
    with zipfile.ZipFile(plugin_path, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)
    return plugin_path
proxyauth_plugin_path = create_proxyauth_extension(
        tunnelhost="********",  # 隧道域名
        tunnelport="*****",  # 端口号
        proxy_username="******",  # 用户名
        proxy_password="*****"  # 密码
    )
class SeleniumDownloaderMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        cls.seleniumRequestCookie = crawler.settings.get("SELENIUM_REQUEST_COOKIE", True)
        cls.seleniumCookieClear = crawler.settings.get("SELENIUM_COOKIE_CLEAR", True)
        cls.seleniumRequests = crawler.settings.get("SELENIUM_REQUESTS", 5)
        cls.seleniumHeadless =crawler.settings.get("SELENIUM_HEADLESS",False)
        cls.seleniumProxy =crawler.settings.get("SELENIUM_PROXY",True)
        cls.seleniumImg =crawler.settings.get("SELENIUM_IMG",False)
        cls.seleniumExceptException=crawler.settings.get("SELENIUM_EXCEPTION_EXCEPT",True)
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(s.spider_closed, signal=signals.spider_closed)
        return s
    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
        self.threadPool = ThreadPoolExecutor(max_workers=self.seleniumRequests, thread_name_prefix="seleniumMultiThread")
    def spider_closed(self):
        self.deleteAllChromeDriver()

    chromeDrivers=[]  #{"status":1/0,"driver":driver} 的list结构 status 1 表示可用 status 0 表示不可用 在被占用

    lock = _thread.allocate_lock()


    @classmethod
    def createChromeDriver(cls,request):
        import logging
        from selenium.webdriver.remote.remote_connection import LOGGER
        LOGGER.setLevel(logging.WARNING)
        option = ChromeOptions()
        option.add_experimental_option('excludeSwitches', ['enable-automation'])
        #option.add_extension(proxyauth_plugin_path)
        if cls.seleniumProxy and request.meta.get("proxy",False):
            option.add_argument('--proxy-server=%s' % request.meta["proxy"])
        if not cls.seleniumImg:
            prefs = {"profile.managed_default_content_settings.images": 2}
            option.add_experimental_option("prefs", prefs)
        if cls.seleniumHeadless:
            option.add_argument("--headless")
        driver = Chrome(options=option)
        return driver
    @classmethod
    def getChromeDriver(cls,request):
        if not cls.getChromeDriverLength():
            driver=cls.createChromeDriver(request)
            cls.appendChromeDriver(driver)
            return driver
        else:
            driver=cls.getStatus1ChromeDriver()
            if(driver==None):
                driverx=cls.createChromeDriver(request)
                cls.appendChromeDriver(driverx)
                return driverx
            else :
                return driver
    @classmethod
    def getChromeDriverLength(cls):
        cls.lock.acquire()
        lenx=len(cls.chromeDrivers)
        cls.lock.release()
        return lenx
    @classmethod
    def appendChromeDriver(cls,driver):
        cls.lock.acquire()
        cls.chromeDrivers.append({"status":0,"driver":driver})
        cls.lock.release()
        return driver
    @classmethod
    def getStatus1ChromeDriver(cls):
        cls.lock.acquire()
        returnDriver=None
        for v in cls.chromeDrivers:
            if v["status"]:
                v["status"]==0
                returnDriver= v["driver"]
        cls.lock.release()
        return returnDriver
    @classmethod
    def setChromeDriverStatus(cls,status, driver):
        cls.lock.acquire()

        for v in SeleniumDownloaderMiddleware.chromeDrivers:
            if v["driver"]==driver:
                v["status"] = status
                if status and len(cls.chromeDrivers)>cls.seleniumRequests:
                    cls.chromeDrivers.remove(v)
                    driver.quit()
                break
        cls.lock.release()
    @classmethod
    def deleteChromeDriver(cls,driver):
        cls.lock.acquire()

        for v in cls.chromeDrivers:
            if v["driver"] == driver:
                cls.chromeDrivers.remove(v)
                driver.quit()
                break
        cls.lock.release()

    @classmethod
    def deleteAllChromeDriver(cls):
        cls.lock.acquire()

        for v in cls.chromeDrivers:
            v["driver"].quit()
        cls.lock.release()
    @classmethod
    def process_request_asynch(self,request,spider,d):


        driver = self.getChromeDriver(request)
        if self.seleniumRequestCookie:
            driver.add_cookie(request.cookies)
        if  self.seleniumCookieClear:
            driver.delete_all_cookies()
        try:

            driver.get(request.url)
            if request.meta.get("driverOperation",False):
                request.meta.get("driverOperation")(driver)

            pageSource=driver.page_source
            htmlResponse = HtmlResponse(
                driver.current_url,
                body=str.encode(pageSource),
                encoding='utf-8',
                request=request
            )

            self.setChromeDriverStatus(1, driver)
            htmlResponse.meta["seleniumResponse"]=True
            d.callback(result=htmlResponse)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.deleteChromeDriver(driver)
            if(self.seleniumExceptException):
                d.callback(result=request)
            else:
                d.errback(fail=e)
                #raise e

    def process_request(self, request, spider):
        if  request.meta.get("selemiumRequest",False) :
            d=defer.Deferred()
            self.threadPool.submit(self.process_request_asynch,request,spider,d)
            return d
        else:
            return None

    def process_response(self, request, response, spider):
        return response
    def process_exception(self, request, exception, spider):
        pass