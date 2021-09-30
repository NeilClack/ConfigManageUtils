import logging
from flask import Flask
from .extensions import authorized
from flask_migrate import Migrate
import os
from . import log


def create_app(test_config=None):

    app = Flask(__name__, instance_relative_config=True)

    if test_config is not None:
        app.config.from_object(test_config)
    else:
        try:
            app.config.from_pyfile("dev.py")
            print("Loaded custom configuration")
        except:
            pass

    # Instance directory and logging setup
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    log_dir = os.path.join(app.instance_path, "logs/")

    try:
        os.makedirs(log_dir)
    except OSError:
        print(
            """Unable to create logs directory. Either the directory already exists,
        the instance path does not exist (run again to fix), or an os error has occurred preventing the creation of the directory."""
        )
        pass

    from . import log

    error_formatter = """%(asctime)s %(levelno)s:%(levelname)s %(filename)s %(lineno)d
        %(message)s"""

    application_formatter = (
        """%(asctime)s %(levelno)s:%(levelname)s %(message)s"""
    )

    app_log = log.CustomLogger(
        name="alog",
        log_file=os.path.join(log_dir, "application.log"),
        level=logging.INFO,
        formatter=logging.Formatter(application_formatter),
    ).create_logger()

    err_log = log.CustomLogger(
        name="elog",
        log_file=os.path.join(log_dir, "error.log"),
        level=logging.WARNING,
        formatter=logging.Formatter(error_formatter),
    ).create_logger()

    # Application setup
    with app.app_context():
        from .extensions import db, ma
        from .params.routes import params

        app_log.info("Application started")

        app.register_blueprint(params)
        db.init_app(app)
        migrate = Migrate(app, db)
        ma = ma.init_app(app)

        @app.route("/sanitycheck", methods=["GET"])
        def test():
            return "Working", 200

        return app
