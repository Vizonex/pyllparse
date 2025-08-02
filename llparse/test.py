from .C_compiler import Compilation, ICompilerOptions
from .frontend import Frontend
from .llparse import LLParse
from .pybuilder import Builder

# TODO: Remove and make pytest for it.


def smaller_test():
    # from compilator import Compilation, ICompilerOptions
    p = Builder()
    simple = p.node("simple")
    complete = p.invoke(
        p.code.match("On_Complete"), {0: simple}, p.error(1, "On_Complete FAILED!")
    )

    simple.peek("\n", complete).skipTo(simple)

    front = Frontend("http_parser")
    f = front.compile(simple, properties=p.properties)
    comp = Compilation(
        "http_parser", f.properties, f.resumptionTargets, ICompilerOptions(None, None)
    )
    # for r in comp.resumptionTargets:
    #     print(r)
    out = []
    root = comp.unwrapNode(f.root)
    root.build(comp)
    comp.reserveSpans(f.spans)
    comp.buildGlobals(out)
    comp.buildResumptionStates(out)
    print(comp.stateDict)
    # print("\n".join(out))


def test1():
    # I will be using indutny's mini http parser to demonstrate as it's
    # medium sized and uses all major tricks , bells and whistles...

    p = Builder()
    method = p.node("method")
    beforeUrl = p.node("before_url")
    urlSpan = p.span(p.code.span("on_url"))
    url = p.node("url")
    http = p.node("http")

    # print(sliced)(method)

    # // Add custom uint8_t property to the state
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

    front = Frontend("http_parser")
    f = front.compile(
        method,
        properties=p.properties,
    )
    # r = f.root.ref.id.name
    # NOTE Check that root was addded , this can be a problem laster down the line if it isn't a resumption target...
    assert f.root in f.resumptionTargets
    comp = Compilation(
        "http_parser", p.properties(), f.resumptionTargets, ICompilerOptions()
    )
    root = comp.unwrapNode(f.root)
    root.build(comp)

    assert "s_n_http_parser__n_method" in comp.resumptionTargets
    out = []
    comp.reserveSpans(f.spans)
    comp.buildGlobals(out)
    out.append("")
    out.append("/*--RESUMPTION STATES--*/")
    comp.buildResumptionStates(out)
    out.append("/*--INTERNAL STATES--*/")
    comp.buildInternalStates(out)
    # for k , v in comp.stateDict.items():
    #     print(k)
    print("\n".join(out))


def test2():
    from llparse import LLParse

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

    c = p.build(method)
    print(c.c)
    open("http_parser.c", "w").write(c.c)
    open("http_parser.h", "w").write(c.header)
    # # sp_alloc = SpanAllocator().allocate(method)

    # TODO Validate Moving parts as they should be compiled correctly...


def test3():
    """Moving Part Validations..."""
    # A~Sample~Of~Dual Spans...
    p = LLParse("dual_spans")

    span_a = p.span(p.code.span("on_a"))
    span_b = p.span(p.code.span("on_b"))

    a = p.node("a_node")
    b = p.node("b_node")

    start = p.node("start")
    start.otherwise(span_a.start(a))

    a.peek("~", span_a.end().skipTo(span_b.start(b))).skipTo(a)
    b.peek("~", span_b.end().skipTo(span_a.start(a))).skipTo(b)

    compiled = p.build(start)
    print(compiled.c)


def test4():
    """Same Dual Spans but with flags..."""
    # A~Sample~Of~Dual Spans...

    p = LLParse("dual_spans")

    # Flag
    p.property("i8", "flag")

    span_a = p.span(p.code.span("on_a"))
    span_b = p.span(p.code.span("on_b"))

    a = p.node("a_node")
    b = p.node("b_node")

    # Invoke Updates to Flag
    # 1 is a , 2 is b

    update_a = p.invoke(p.code.update("flag", 1), span_a.start(a))
    update_b = p.invoke(p.code.update("flag", 2), span_b.start(b))
    start = p.node("start")
    start.otherwise(update_a)

    a.peek("~", span_a.end().skipTo(update_a)).skipTo(a)
    b.peek("~", span_b.end().skipTo(update_b)).skipTo(b)

    compiled = p.build(start)
    print(compiled.c)


# TODO  Try to Throw more complicated and advanced things at pyllparse to try and solve
# This will make the code sturdier and more mature as time goes on
# Make a Test Bag on github for all of these tests to go into incase a single file gets too big

# I encourage anyone to find valid compiled llparse sequences and then translate them over to
# python to testrun , I will try to make a validator tool whenever I can get to it - Vizonex

if __name__ == "__main__":
    test2()
