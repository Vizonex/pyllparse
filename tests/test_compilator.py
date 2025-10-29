# The good old http_parser was borrowed from llparse.org to demonstrate this for you :)
from llparse import LLParse


def test_http_parser_example():

    p = LLParse("http_parser")
    method = p.node("method")
    beforeUrl = p.node("before_url")
    urlSpan = p.span(p.code.span("on_url"))
    url = p.node("url")
    http = p.node("http")

    # Add custom uint8_t property to the state
    p.property("i8", "method")

    # Store method inside a custom property
    onMethod = p.invoke(p.code.store("method"), beforeUrl)

    # Invoke custom C function
    complete = p.invoke(
        p.code.match("on_complete"),
        {
            #  Restart
            0: method
        },
        p.error(4, "`on_complete` error"),
    )

    method.select(
        {
            "HEAD": 0,
            "GET": 1,
            "POST": 2,
            "PUT": 3,
            "DELETE": 4,
            "OPTIONS": 5,
            "CONNECT": 6,
            "TRACE": 7,
            "PATCH": 8,
        },
        onMethod,
    ).otherwise(p.error(5, "Expected method"))

    beforeUrl.match(" ", beforeUrl).otherwise(urlSpan.start(url))

    url.peek(" ", urlSpan.end(http)).skipTo(url)

    http.match(" HTTP/1.1\r\n\r\n", complete).otherwise(
        p.error(6, "Expected HTTP/1.1 and two newlines")
    )

    # if this build fails in any way then we have failed...
    c = p.build(method)