import json
import time
import urllib
from json.decoder import JSONDecodeError
from typing import Optional

from graphqlclient import GraphQLClient
from locust import User


class MeasuredGraphQLClient(GraphQLClient):
    def __init__(self, endpoint, request_event):
        super().__init__(endpoint)
        self._request_event = request_event

    def execute(self, label, query, variables=None, type="graphql") -> Optional[dict]:
        start_time = time.time()
        result = None
        try:
            data = super().execute(query, variables)
            result = json.loads(data)
        except (urllib.error.HTTPError, urllib.error.URLError, ValueError, JSONDecodeError) as e:
            total_time = int((time.time() - start_time) * 1000)
            self._request_event.fire(
                request_type=type, name=label, response_time=total_time, exception=e
            )

        else:
            total_time = int((time.time() - start_time) * 1000)
            if "errors" in result:
                self._request_event.fire(
                    request_type=type,
                    name=label,
                    response_time=total_time,
                    exception=result["errors"],
                    response_length=len(result),
                )
            else:
                self._request_event.fire(
                    request_type=type, name=label, response_time=total_time, response_length=0
                )
        return result


class GraphQLLocust(User):
    abstract = True
    endpoint = ""

    def __init__(self, *args, **kwargs):
        super(GraphQLLocust, self).__init__(*args, **kwargs)
        destination_endpoint = f"{self.host}{self.endpoint}"
        self.client = MeasuredGraphQLClient(
            endpoint=destination_endpoint,
            request_event=self.environment.events.request,
        )
