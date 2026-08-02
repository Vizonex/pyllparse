# Work in progress do not use...
# from llparse_builder.builder import Builder
# from llparse_frontend.container import Container
# from llparse_frontend.frontend import Frontend

# from .fixtures import implementation


# def test_node_translation(b: Builder):
#     comb = Container()
#     comb.add('a', implementation)
#     comb.add('b', implementation)

#     f = Frontend('llparse', comb.build())

#     root = b.node('root')

#     root.match('ab', root)
#     root.match('acd', root)
#     root.match('efg', root)
#     root.otherwise(b.error(123, 'hello'))

#     f_root = f.compile(root, []).root

#     out: list[str] = []
#     f_root.get('a').build(out)


#     assert '<Single name=llparse__n_root k97=llparse__n_root_1'\
#         ' k101=llparse__n_root_3 otherwise-no_adv='\
#         'llparse__n_error/>' in out

