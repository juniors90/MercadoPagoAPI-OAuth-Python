#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of the Flask-Mercadopago Project
#    (https://github.com/juniors90/MercadoPagoAPI-OAuth-Python/).
# Copyright (c) 2022, Ferreira Juan David
# License: MIT
# Full Text:
#    https://github.com/juniors90/MercadoPagoAPI-OAuth-Python-Example/blob/master/LICENSE

# =============================================================================
# DOCS
# =============================================================================

"""MercadoPagoAPI-OAuth2-Python-Example

Implementation of Mercado Pago API OAuth  in Flask.
"""

# =============================================================================
# IMPORTS
# =============================================================================

import datetime
import json
import logging
import os
import uuid

from dotenv import load_dotenv

from flask import (
    Flask,
    current_app,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

import requests


load_dotenv()
app = Flask(__name__)
app.secret_key = "super-secret"

SERVER_URL = "http://localhost:5000"

settings = {
    "title": "Mercadopago API with Python",
    "base_url": "https://api.mercadopago.com/v1",
    "authorization_endpoint": "https://auth.mercadopago.com.ar/authorization",
    "token_endpoint": "https://api.mercadopago.com/oauth/token",
    "APP_ACCESS_TOKEN": os.environ.get("APP_ACCESS_TOKEN"),
    "client_id": os.environ.get("CLIENT_ID"),
    "client_secret": os.environ.get("CLIENT_SECRET"),
    "callback_url": os.environ.get("CALLBACK_URL"),
    "response_type": "code",
    "state": uuid.uuid1(),
    "org_connection_completed_url": os.environ.get("ORG_CONNECTION_COMPLETED_URL"),
    "access_token": "",
    "token_type": "",
    "expires_in": "",
    "scope": "",
    "user_id": "",
    "refresh_token": "",
    "public_key": "",
    "live_mode": "",
    "access_token_details": "",
    "code": "",
    "api_response": "",
}


# Leave the line below as-is. This line of code verifies
# that you've modified the APP_ACCESS_TOKEN, CALLBACK_URL,
# CLIENT_ID, CLIENT_SECRET, CLIENT_REDIRECT_URI to the
# values above so that your application can complete OAuth.
assert (
    os.environ["APP_ACCESS_TOKEN"] != "place_app_access_token_here"
), "You need to update your config key APP_ACCESS_TOKEN in this line"
assert (
    os.environ.get("CALLBACK_URL") != "place_client_redirect_uri_here"
), "You need to update your config key CALLBACK_URL in this line"
assert (
    os.environ.get("CLIENT_ID") != "place_client_id_here"
), "You need to update your config key CLIENT_ID in this line"
assert (
    os.environ.get("CLIENT_SECRET") != "place_client_secret_here"
), "You need to update your config key CLIENT_SECRET in this line"
assert (
    os.environ.get("ORG_CONNECTION_COMPLETED_URL") != "place_org_url_here"
), "You need to update your config key ORG_CONNECTION_COMPLETED_URL in this line"


def update_token_info(res):
    json_response = res.json()
    seconds = json_response["expires_in"]
    expire_in = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
    session["access_token"] = json_response["access_token"]
    session["expires_in"] = expire_in
    session["token_type"] = json_response["token_type"]
    session["refresh_token"] = json_response["refresh_token"]
    session["scope"] = json_response["scope"]
    session["user_id"] = json_response["user_id"]
    session["refresh_token"] = json_response["refresh_token"]
    session["public_key"] = json_response["public_key"]
    session["live_mode"] = json_response["live_mode"]
    access_token_details = {
        "access_token": json_response["access_token"],
        "token_type": json_response["token_type"],
        "scope": json_response["scope"],
        "user_id": json_response["user_id"],
        "refresh_token": json_response["refresh_token"],
        "public_key": json_response["public_key"],
        "live_mode": json_response["live_mode"],
    }
    session["access_token_details"] = json.dumps(access_token_details, indent=4)


def update_settings_info(api_response=None):
    settings["access_token"] = session["access_token"]
    settings["token_type"] = session["token_type"]
    settings["expires_in"] = session["expires_in"]
    settings["scope"] = session["scope"]
    settings["user_id"] = session["user_id"]
    settings["refresh_token"] = session["refresh_token"]
    settings["public_key"] = session["public_key"]
    settings["live_mode"] = session["live_mode"]
    settings["access_token_details"] = session["access_token_details"]
    settings["api_response"] = "" if api_response is None else api_response


def delete_settings_info():
    settings.pop("access_token")
    settings.pop("token_type")
    settings.pop("expires_in")
    settings.pop("scope")
    settings.pop("user_id")
    settings.pop("refresh_token")
    settings.pop("public_key")
    settings.pop("live_mode")
    settings.pop("access_token_details")
    settings.pop("api_response")


def get_location(endpoint):
    return settings[endpoint]


def api_get(access_token, resource_url):
    headers = {
        "Authorization": "Bearer " + access_token,
        "Content-Type": "application/json",
    }
    res = requests.get(resource_url, headers=headers)
    return res


def render_error(message, title=None):
    _title = settings["title"] if title is None else title
    ctx = {
        "title": _title,
        "error": message,
    }
    return render_template("error.html", **ctx)


def get_oidc_query_string():
    query_params = {
        "response_type": settings["response_type"],
        "client_id": settings["client_id"],
        "state": settings["state"],
        "redirect_uri": settings["callback_url"],
    }
    params = [f"{key}={value}" for key, value in query_params.items()]
    return "&".join(params)


@app.route("/", methods=["POST"])
def start_oidc():
    settings["response_type"] = request.form["response_type"]
    settings["client_id"] = request.form["client_id"]
    settings["state"] = request.form["state"]
    settings["callback_url"] = request.form["callback_url"]
    redirect_url = f"{get_location('authorization_endpoint')}?{get_oidc_query_string()}"
    return redirect(redirect_url, code=302)


@app.route("/callback")
def process_callback():
    try:
        code = request.args["code"]
        headers = {
            "Authorization": "Bearer " + settings["APP_ACCESS_TOKEN"],
            "Content-Type": "application/json",
        }
        payload = {
            "client_id": settings["client_id"],
            "client_secret": settings["client_secret"],
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings["callback_url"],
        }
        token_endpoint = get_location("token_endpoint")
        res = requests.post(token_endpoint, headers=headers, params=payload)
        update_token_info(res)
        update_settings_info()
        organization_access_url = settings["org_connection_completed_url"]
        if organization_access_url is not None:
            return redirect(organization_access_url, code=302)
        return index()
    except Exception as e:
        logging.exception(e)
        return render_error("Error getting token!")


@app.route("/call-api", methods=["POST"])
def call_the_api():
    try:
        url = request.form["url"]
        headers = {
            "Authorization": "Bearer " + settings["access_token"],
            "Content-Type": "application/json",
        }
        res = requests.get(url, headers=headers)
        res_json = res.json()
        session["api_response"] = json.dumps(res_json, indent=4)
        update_settings_info(api_response=session["api_response"])
        return index()
    except Exception as e:
        logging.exception(e)
        return render_error("Error calling API!")


@app.route("/refresh-access-token")
def refresh_access_token():
    try:
        headers = {
            "Authorization": "Bearer " + settings["APP_ACCESS_TOKEN"],
            "Content-Type": "application/json",
        }
        payload = {
            "client_id": settings["client_id"],
            "client_secret": settings["client_secret"],
            "code": settings["code"],
            "grant_type": "refresh_token",
            "redirect_uri": settings["callback_url"],
            "refresh_token": settings["refresh_token"],
        }
        token_endpoint = get_location("token_endpoint")
        res = requests.post(token_endpoint, params=payload, headers=headers)
        update_token_info(res)
        update_settings_info()
        return redirect(url_for("index"))
    except Exception as e:
        logging.exception(e)
        return render_error("Error getting refresh token!")


@app.route("/preferences")
def preferences():
    try:
        url = "https://api.mercadopago.com/checkout/preferences"
        params = {
            "items": [
                {
                    "title": "Dummy Title",
                    "description": "Dummy description",
                    "picture_url": "http://www.myapp.com/myimage.jpg",
                    "category_id": "car_electronics",
                    "quantity": 1,
                    "currency_id": "ARS",
                    "unit_price": 10,
                }
            ],
            "payer": {
                "name": "",
                "surname": "",
                "email": "",
                "phone": {},
                "identification": {},
                "address": {"zip_code": "", "street_name": "", "street_number": 1000},
            },
            "payment_methods": {
                "excluded_payment_methods": [{}],
                "excluded_payment_types": [{}],
            },
            "shipments": {"free_methods": [{}], "receiver_address": {}},
            "back_urls": {
                "failure": "http://localhost:5000/failure",
                "pending": "http://localhost:5000/pending",
                "success": "http://localhost:5000/success",
            },
            "differential_pricing": {},
            "metadata": {},
        }
        headers = {
            "Authorization": "Bearer " + settings["access_token"],
            "Content-Type": "application/json",
        }
        res = requests.post(url, headers=headers, json=params)
        session["api_response"] = json.dumps(res.json(), indent=4)
        update_settings_info(api_response=session["api_response"])
        return index()
    except Exception as e:
        logging.exception(e)
        return render_error("Error calling API!")


@app.route("/")
def index():
    if session.get("live_mode") and settings["api_response"] == "":
        update_settings_info()
    return render_template("main.html", **settings)


@app.route("/logout")
def logout():
    session.clear()
    delete_settings_info()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True)
