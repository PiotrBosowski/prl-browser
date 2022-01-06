from bottle import *
import os
import settings
from domain.training_model import Training
from training_utils.combined_outputs import overview_csv


@get(f'/<session_name>/<model_name>/refresh')
def invalidate_cache(session_name, model_name):
    global global_models
    global_models = Training.load_all()
    return redirect(f"/{session_name}/{model_name}")


@post(f'/<session_name>/<model_name>/delete')
def delete_model(session_name, model_name):
    deleted = Training.delete_model(global_models, session_name, model_name)
    if deleted:
        return redirect(
            f"/{request.forms.next_session}/{request.forms.next_model}")
    else:
        return redirect('/')


@route(f'/<session>/<model>/<filename>')
def send_image(session, model, filename):
    """
    Sends an image.
    :param session:
    :param model: model name
    :param filename: image name
    :return: static file of the requested image
    """
    model_path = os.path.join(settings.models_dir, session, model)
    return static_file(filename, root=model_path, mimetype='image/png')


@route(f'/<session>/<model>/<report>/<filename>')
def send_report_image(session, model, report, filename):
    """
    Sends an image.
    :param session:
    :param model: model name
    :param filename: image name
    :return: static file of the requested image
    """
    model_path = os.path.join(settings.models_dir, session, model, report)
    return static_file(filename, root=model_path, mimetype='image/png')


@get(f'/<session_name>/<model_name>')
@view('model_template')
def model_page(session_name, model_name):
    """
    Returns model view page.
    :param session_name:
    :param model_name: model name
    :return: model view generated from model_template
    """
    Training.refresh_models(global_models)
    current_model = global_models[session_name][model_name]
    test_id = request.query.test
    if test_id and current_model.reports:
        current_test = current_model.reports[int(test_id)]
        current_test_url = os.path.basename(current_test.path)
    elif current_model.reports:
        current_test = current_model.get_last_report()
        current_test_url = os.path.basename(current_test.path)
    else:
        current_test = None
        current_test_url = ""
    models = Training.models_flat(global_models)
    models = Training.models_select(models, recent, filter, sortby)
    # datasets_structures = {name: json.dumps(dataset['sources'], indent=2)
    #                        for name, dataset in current_model.datasets.items()}
    datasets = current_model.datasets

    if current_model in models:
        index = models.index(current_model)
        return template('browser/model_template',
                        models=models,
                        model=current_model,
                        datasets=datasets,
                        # datasets_structures=datasets_structures,
                        validation=current_model.history[-1].report.confusion,
                        previous=models[index - 1],
                        following=Training.get_next_model(index, models),
                        current_test=current_test,
                        current_test_url=current_test_url,
                        settings=settings)
    else:
        return redirect('/')


@route('/favicon.ico', method='GET')
def get_favicon():
    """
    Browsers for no reason keep asking for favicon, so there you go.
    :return: favicon
    """
    return static_file('favicon.ico', root='browser')


@route('/style.css')
def send_style():
    """
    Sends style.css.
    :return: style.css
    """
    return static_file('style.css', root='browser')


@route('/navigation.js')
def send_js():
    return static_file('navigation.js', root='browser')


@route('/jquery-3.5.1.min.js')
def send_js():
    return static_file('jquery-3.5.1.min.js', root='browser')


@get('/overview.csv')
def generate_csv():
    filename = overview_csv(global_models)
    return static_file(filename, root=settings.models_dir)


@route('/')
@view('report_template')
def index():
    """
    Returns main page of the server.
    :return:
    """
    Training.refresh_models(global_models)
    models = Training.models_flat(global_models)
    models = Training.models_select(models, recent, filter, sortby)
    if models:
        return redirect(models[0].url())
    else:
        return "no models to show"


def browse_results():
    """
    Launches the server at localhost:8080.
    """
    run(host='localhost', port=8080)


if __name__ == "__main__":
    recent = 0
    filter = ""
    sortby = "accuracy"
    reverse_order = True
    global_models = Training.load_all(skip_raw_outputs=True,
                                      skip_wrong_preds=True)
    browse_results()

