from flask import abort, jsonify, request
from jfkpay.model import generate_validator
from flask.views import MethodView


class ItemAPI(MethodView):
    init_every_request = False

    def __init__(self, model):
        self.model = model
        self.validator = generate_validator(model)

    def _get_item(self, uuid):
        if result := self.model.db.get_or_404(uuid) is None:
            abort(404)
        else:
            return result

    def get(self, uuid):
        item = self._get_item(uuid)
        return jsonify(item.to_json())

    def patch(self, uuid):
        item = self._get_item(uuid)
        errors = self.validator.validate(item, request.json)

        if errors:
            return jsonify(errors), 400

        item.update_from_json(request.json)
        item.update()
        return jsonify(item.to_json())

    def delete(self, uuid):
        item = self._get_item(uuid)
        self.model.db.delete(item)
        return "", 204


class GroupAPI(MethodView):
    init_every_request = False

    def __init__(self, model):
        self.model = model
        self.validator = generate_validator(model, create=True)

    def get(self):
        items = self.model.all()
        return jsonify([item for item in items])

    def post(self):
        errors = self.validator.validate(request.json)

        if errors:
            return jsonify(errors), 400

        item = self.model.db.add(self.model.from_json(request.json))
        return jsonify(item.to_json())
