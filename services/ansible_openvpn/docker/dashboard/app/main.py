#  BSD 3-Clause License
#
#  Copyright (c) 2023, University Gustave Eiffel
#  All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#
#   Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
#   Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
#  FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
#  DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#  SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#  CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#  OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#  OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import os
from elasticsearch import Elasticsearch
from elasticsearch.helpers import streaming_bulk
import elasticsearch.helpers

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.mount("/fonts", StaticFiles(directory="app/fonts"), name="fonts")

templates = Jinja2Templates(directory="app/templates")

if not os.path.exists("app/config.json"):
    raise Exception("Configuration file not found " +
                    os.path.abspath("app/config.json"))
configuration = json.load(open("app/config.json", "r"))

client = Elasticsearch(
    configuration.get("url", "https://es01:9200"),
    api_key=(configuration["id"], configuration["api_key"]),
    verify_certs=configuration.get("verify_certs", True), timeout=60
)


@app.get("/api/sensor_position")
async def get_sensor_position(request: Request):
    post_data = templates.get_template("query_sensor_list.json").render()
    resp = client.search(index="sensor_location_*", query=post_data)
    return resp

@app.get('/', response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("status.html",
                                      context={"request": request})

