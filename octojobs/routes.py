"""Adding routes for the configuration to find."""


def includeme(config):
    """The module defines the routes that tie in to the views on defaul.py."""
    config.add_static_view(name='static', path='octojobs:static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('about', '/about')
    config.add_route('results', '/results')
