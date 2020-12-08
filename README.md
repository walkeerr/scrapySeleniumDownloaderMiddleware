# scrapySeleniumDownloaderMiddleware
 scrapy 异步 selenium chrome 下载中间件(scrapy  asynchronous selenium chrome downloaderMiddleware )
## 介绍(Introduction)
scarpyseleniumDownloaderMiddleware 是一个scrapy可以使用的selenium进行异步下载的下载中间件,只需要像使用其他下载中间件一样使用它即可,但与普通下载中间件不同的是使用了twisted的refered对象和线程池来实现 下载中间件在scrapy中的异步化.
ScarphyseleniumDownloaderMiddleware is a downloadermiddleware which can be downloaded asynchronously by selenium. It can be used just like other scrapy download middleware. But different from the common scrapy download middleware, it uses twisted referenced object and thread pool to realize asynchronous downloading Middleware in scrapy

## 前提(Precondition)
scrapySeleniumDownloaderMiddleware需要你有可以搭建起基本的scrapy和selenium项目的环境和能力,本项目只是将selenium依据scrapy的下载中间件机制融合到scrapy当中 
ScrapseleniumDownloaderMiddleware requires you to have the environment and ability to build basic scrapy and selenium projects. This project only integrates selenium's download mechanism into scrapy.
测试环境(testing environment) `python 3.8` `scarpy 2.4.1`  `selenium 3.141.0`
## 使用流程(Use Flow)
1. 将scrapySeleniumDownloaderMiddleware 拷贝到 scrapy 项目中(Copy the scrapyselenium downloadermiddleware into the scrapy project)
2. 在settings.py中启用该中间件( enable the middleware in settings.py)
``` 
DOWNLOADER_MIDDLEWARES = {
    'spiderproject.scrapySeleniumDownloaderMiddleware.SeleniumDownloaderMiddleware': 543,
}
```
3. 在settings.py中进行相关配置( relevant configuration in settings.py)
```
#selenium请求是否会使用 cookie的请求(Will selenium requests use scrapy request cookie )
SELENIUM_REQUEST_COOKIE=False 
# selenium使用一个浏览器进行不同request时是否会清除COOKIE(Does selenium clear the cookie when using a browser for different requests)
SELENIUM_COOKIE_CLEAR=False 
# selenium并发的请求数(Selenium concurrent requests)
SELENIUM_REQUESTS=2 
# selenium是否使用无头模式(Does selenium use headless mode)
SELENIUM_HEADLESS=True 
# selenium是否使用 request meta中的代理(Does selenium use proxy in request meta)
SELENIUM_PROXY=False 
#selenium是否会加载图片(Will selenium load images)
SELENIUM_IMG=False  
#当selenium中发生异常 是捕获异常将request重新调度,还是不捕获异常丢弃request(When an exception occurs in selenium, do you catch the exception and reschedule the request, or do not catch the exception and discard the request)
SELENIUM_EXCEPTION_EXCEPT=False 
```
4. 使用request中meta字段来标识该request是一个seleniumRequest(Use the meta field in the request to identify that the request is a selenium request)
```
seleniumRequest=scrapy.Request(
                             url="url",
                             meta={"selemiumRequest":True},
                             callback=self.nextParse)
```
5. 创建seleniumRequest时可以接受一个回调方法,作为selenium加载完页面后的回调方法(When creating selenium request, you can accept a callback method as a callback method after selenium has loaded the page)
```
seleniumRequestHaveDriverCallback=scrapy.Request(
                             url="url",
                             meta={"selemiumRequest":True,"driverOperation":driverCallback}, 
                             callback=self.nextParse)
```
  driverCallback必须是一个传参是driver(webDriver对象)的全局方法(局部方法会无法序列化,你可以自定以其相关功能(Drivercallback must be a global method whose parameter is the driver (webdriver object). Local methods cannot be serialized.)
```
def driverCallback(driver):
  #driverOperation....
```
6. 本中间件只支持已系统注册的chrome浏览器作为selenium的浏览器,如需自定义请修改scrapySeleniumDownloaderMiddleware.seleniumDownloaderMiddleware的类方法createChromeDriver方法(This middleware only supports Chrome browser registered by the system as selenium's browser. If you need to customize it, please modify the method createchromedriver of scrapselenium DownloaderMiddleware.seleniumDownloaderMiddleware  class 
