if __name__ == '__main__':
    from src.platform_compat import configure_runtime

    configure_runtime()

    from config import config
    from ok import OK

    config = config
    ok = OK(config)
    ok.start()
