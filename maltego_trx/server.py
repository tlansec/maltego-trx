import logging

from flask import Flask, request
from maltego_trx.maltego import MaltegoMsg
from .registry import mapping

log = logging.getLogger("maltego.server")
logging.basicConfig(level=logging.DEBUG)

URL_TEMPLATE = '/run/<transform_name>/'


def get_exception_message(msg="An exception occurred with the transform. Check the logs for more details."):
    return """<MaltegoMessage>
    <MaltegoTransformResponseMessage>
        <Entities>
        </Entities>
        <UIMessages>
            <UIMessage MessageType='PartialError'>
                %s
            </UIMessage>
        </UIMessages>
    </MaltegoTransformResponseMessage>
</MaltegoMessage>""" % msg


def print_transforms():
    print("= Transform Server URLs =")
    for path in mapping:
        print(URL_TEMPLATE.replace("<transform_name>", path) + ": " + mapping[path].__name__)
    print("\n")

    print("= Local Transform Names =")
    for path in mapping:
        print(path + ": " + mapping[path].__name__)
    print("\n")


def run_transform(transform_name, client_msg):
    transform_method = mapping[transform_name]
    try:
        if hasattr(transform_method, "run_transform"):
            return transform_method.run_transform(client_msg), 200  # Transform class
        else:
            return transform_method(client_msg), 200  # Transform method
    except Exception as e:
        log.error("An exception occurred while executing your transform code.")
        log.error(e, exc_info=True)
        return get_exception_message(), 200


app = Flask(__name__)
app.url_map.strict_slashes = False  # !NOTE - Added to support args in URL with greater ease.
application = app  # application variable for usage with apache mod wsgi


@app.route(URL_TEMPLATE, methods=['GET', 'POST'])
def transform_runner(transform_name):
    transform_name = transform_name.lower()
    if transform_name in mapping:
        if request.method == 'POST':
            # !NOTE - modified to support TI-734
            client_msg = MaltegoMsg(request.data, request=request)
            return run_transform(transform_name, client_msg)
        else:
            return "Transform found with name '%s', you will need to send a POST request to run it." % transform_name, 200
    else:
        log.info("No transform found with the name '%s'." % transform_name)
        log.info("Available transforms are:\n %s" % str(list(mapping.keys())))
        return "No transform found with the name '%s'." % transform_name, 404


@app.route('/', methods=['GET', 'POST'])
def index():
    return "You have reached a Maltego Transform Server.", 200
