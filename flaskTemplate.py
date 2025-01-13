template = {
  "swagger": "2.0",
  "info": {
    "title": "Liquify thornode API",
    "description": "API to easily access thornode data",
    "specs_route": "/thor/api/docs",
    "contact": {
      "responsibleOrganization": "Liquify LTD",
      "responsibleDeveloper": "Liquify LTD",
      "email": "contact@liquify.io",
      "url": "https://www.liquify.io",
    },
    "version": "1.0"
  },
  "specs_route": "/thor/api/docs",
  "schemes": [
    "https",
    "http"
  ]
}

swagger_config = {
    "headers": [
    ],
    "specs": [
        {
            "endpoint": 'specifications',
            "route": '/specifications.json',
            "rule_filter": lambda rule: True,  # all in
            "model_filter": lambda tag: True,  # all in
        }
    ],
    "static_url_path": "/flasgger_static",
    "specs_route": "/thor/api/docs"
}