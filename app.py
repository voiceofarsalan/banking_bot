from flask import Flask, render_template, request, jsonify
import pandas as pd
import random
from elasticsearch import Elasticsearch,helpers
import warnings
from elasticsearch.helpers import bulk, BulkIndexError
import numpy as np
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import subprocess
import json
warnings.simplefilter('ignore', InsecureRequestWarning)
import re

es = Elasticsearch(
    ['https://localhost:9200'],
    basic_auth=('elastic','TJyZFIZ*U70V1cikx8s8'),
    verify_certs=False
)


def basic_search_tool(index_name, query, fields=None, size=10):
    """Perform a basic search with optional field selection."""
    try:
        body = {
            "query": {
                "bool": {
                    "must": [{"match": {k: v}} for k, v in query.items()]
                }
            },
            "size": size  # Include the size within the body
        }
        if fields:
            body["_source"] = fields
        res = es.search(index=index_name, body=body)
        return res['hits']['hits']
    except Exception as e:
        return f"Error executing basic search: {str(e)}"


def aggregation_tool(index_name, agg_field, agg_type="sum"):
    """Perform aggregations (sum, avg, min, max, count) on a specified field."""
    try:
        body = {
            "size": 0,  # No hits, only aggregations
            "aggs": {
                "result": {
                    agg_type: {"field": agg_field}
                }
            }
        }
        res = es.search(index=index_name, body=body)
        return res['aggregations']['result']
    except Exception as e:
        return f"Error executing aggregation: {str(e)}"


def multi_match_search_tool(index_name, search_term, fields, size=10):
    """Search for a term across multiple fields."""
    try:
        body = {
            "query": {
                "multi_match": {
                    "query": search_term,
                    "fields": fields
                }
            },
            "size": size  # Include the size within the body
        }
        res = es.search(index=index_name, body=body)
        return res['hits']['hits']
    except Exception as e:
        return f"Error executing multi-match search: {str(e)}"


def range_search_tool(index_name, query, range_field, gte=None, lte=None, size=10):
    """Perform a search with range filtering."""
    try:
        range_filter = {}
        if gte:
            range_filter["gte"] = gte
        if lte:
            range_filter["lte"] = lte

        body = {
            "query": {
                "bool": {
                    "must": [{"match": {k: v}} for k, v in query.items()],
                    "filter": {
                        "range": {
                            range_field: range_filter
                        }
                    }
                }
            },
            "size": size  # Include the size within the body
        }
        res = es.search(index=index_name, body=body)
        return res['hits']['hits']
    except Exception as e:
        return f"Error executing range search: {str(e)}"


def query_string_search_tool(index_name, query_string, size=10):
    """Perform a search using Elasticsearch's query string syntax."""
    try:
        body = {
            "query": {
                "query_string": {
                    "query": query_string
                }
            },
            "size": size  # Include the size within the body
        }
        res = es.search(index=index_name, body=body)
        return res['hits']['hits']
    except Exception as e:
        return f"Error executing query string search: {str(e)}"


def filtered_aggregation_tool(index_name, query, agg_field, agg_type="sum"):
    """Perform an aggregation with filtering."""
    try:
        body = {
            "size": 0,  # No hits, only aggregations
            "query": {
                "bool": {
                    "must": [{"match": {k: v}} for k, v in query.items()]
                }
            },
            "aggs": {
                "filtered_agg": {
                    agg_type: {"field": agg_field}
                }
            }
        }
        res = es.search(index=index_name, body=body)
        return res['aggregations']['filtered_agg']
    except Exception as e:
        return f"Error executing filtered aggregation: {str(e)}"


def scroll_search_tool(index_name, query, scroll_time="1m", size=100):
    """Perform a scroll search for large datasets."""
    try:
        body = {
            "query": {
                "bool": {
                    "must": [{"match": {k: v}} for k, v in query.items()]
                }
            },
            "size": size  # Include the size within the body
        }
        page = es.search(index=index_name, body=body, scroll=scroll_time)
        sid = page['_scroll_id']
        scroll_size = len(page['hits']['hits'])

        results = []
        while scroll_size > 0:
            results.extend(page['hits']['hits'])
            page = es.scroll(scroll_id=sid, scroll=scroll_time)
            sid = page['_scroll_id']
            scroll_size = len(page['hits']['hits'])

        return results
    except Exception as e:
        return f"Error executing scroll search: {str(e)}"


def bulk_index_tool(index_name, docs):
    """Bulk index a list of documents."""
    try:
        actions = [
            {
                "_index": index_name,
                "_id": doc['id'],  # Assuming each document has a unique 'id' field
                "_source": doc
            }
            for doc in docs
        ]
        success, _ = bulk(es, actions)
        return f"Successfully indexed {success} documents."
    except Exception as e:
        return f"Error during bulk indexing: {str(e)}"


def search_documents(index_name, query):
    """Search for documents in the specified index using the provided query."""
    body = {
        "query": {
            "match": query  # Use match instead of term to find documents
        }
    }
    res = es.search(index=index_name, body=body)
    return res


def update_documents_by_query(index_name, query, script_source):
    """
    Update documents in the specified index based on a query.

    Parameters:
    - index_name: The name of the index.
    - query: The query to find documents that need to be updated.
    - script_source: The script source that defines the update.
    """
    try:
        # Search first to see if the query matches any documents
        search_res = search_documents(index_name, query)
        print(f"Search Result: {search_res['hits']['total']['value']} documents found.")

        # Proceed with update if documents are found
        if search_res['hits']['total']['value'] > 0:
            body = {
                "query": {
                    "match": query  # Changed from term to match
                },
                "script": {
                    "source": script_source,
                    "lang": "painless"
                }
            }
            res = es.update_by_query(index=index_name, body=body)
            return res
        else:
            return "No documents found to update."
    except Exception as e:
        return f"Error executing update by query: {str(e)}"


def delete_by_query_tool(index_name, query):
    """Delete documents that match the query."""
    try:
        body = {
            "query": {
                "bool": {
                    "must": [{"match": {k: v}} for k, v in query.items()]
                }
            }
        }
        res = es.delete_by_query(index=index_name, body=body)
        return res
    except Exception as e:
        return f"Error executing delete by query: {str(e)}"


def multi_index_search_tool(index_names, query, size=10):
    """Search across multiple indices."""
    try:
        body = {
            "query": {
                "bool": {
                    "must": [{"match": {k: v}} for k, v in query.items()]
                }
            },
            "size": size  # Include the size within the body
        }
        res = es.search(index=index_names, body=body)
        return res['hits']['hits']
    except Exception as e:
        return f"Error executing multi-index search: {str(e)}"


def term_suggestion_tool(index_name, field, term):
    """Provide term suggestions for autocomplete."""
    try:
        body = {
            "suggest": {
                "text": term,
                "term_suggestion": {
                    "term": {
                        "field": field
                    }
                }
            }
        }
        res = es.search(index=index_name, body=body)
        return res['suggest']['term_suggestion']
    except Exception as e:
        return f"Error executing term suggestion: {str(e)}"


def nested_query_tool(index_name, path, query, size=10):
    """Search within nested fields."""
    try:
        body = {
            "query": {
                "nested": {
                    "path": path,
                    "query": {
                        "bool": {
                            "must": [{"match": {f"{path}.{k}": v}} for k, v in query.items()]
                        }
                    }
                }
            },
            "size": size  # Include the size within the body
        }
        res = es.search(index=index_name, body=body)
        return res['hits']['hits']
    except Exception as e:
        return f"Error executing nested query: {str(e)}"


def geo_location_search_tool(index_name, location_field, lat, lon, distance="10km", size=10):
    """Search for documents within a specific radius of a given geo-location."""
    try:
        body = {
            "query": {
                "bool": {
                    "filter": {
                        "geo_distance": {
                            "distance": distance,
                            location_field: {
                                "lat": lat,
                                "lon": lon
                            }
                        }
                    }
                }
            },
            "size": size  # Include the size within the body
        }
        res = es.search(index=index_name, body=body)
        return res['hits']['hits']
    except Exception as e:
        return f"Error executing geo-location search: {str(e)}"


def complex_aggregation_tool(index_name, aggs_body):
    """Perform complex aggregations involving multiple fields and sub-aggregations."""
    try:
        body = {
            "size": 0,  # No hits, only aggregations
            "aggs": aggs_body
        }
        res = es.search(index=index_name, body=body)
        return res['aggregations']
    except Exception as e:
        return f"Error executing complex aggregation: {str(e)}"


prompt_template = """
You are an intelligent assistant designed to process user queries related to Elasticsearch operations and determine the appropriate tool to use along with correctly formatted parameters. If you get any question out of context e.g "Who is Quaid-e-azam" then reply youre an Banking chatbot and you cant answer these questions.

You are interacting with an Elasticsearch index named `banking_data`. This index contains detailed financial and personal information about customers. The following tools are available to query the data:

### Available Tools:

1. **basic_search_tool**
   - **Description**: Performs a basic search with optional field selection.
   - **Parameters**:
     - `index_name` (string) **[Required]**: Name of the Elasticsearch index.
     - `query` (object) **[Required]**: Key-value pairs to match documents.
     - `fields` (list of strings) **[Optional]**: Specific fields to include in the response.
     - `size` (integer) **[Optional]**: Number of results to return. Default is 10.

2. **aggregation_tool**
   - **Description**: Performs aggregations (sum, avg, min, max, count) on a specified field.
   - **Parameters**:
     - `index_name` (string) **[Required]**: Name of the Elasticsearch index.
     - `agg_field` (string) **[Required]**: Field to perform aggregation on.
     - `agg_type` (string) **[Optional]**: Type of aggregation (`sum`, `avg`, `min`, `max`, `count`). Default is `sum`.

3. **multi_match_search_tool**
   - **Description**: Searches for a term across multiple fields.
   - **Parameters**:
     - `index_name` (string) **[Required]**: Name of the Elasticsearch index.
     - `search_term` (string) **[Required]**: The term to search for.
     - `fields` (list of strings) **[Required]**: Fields to search across.
     - `size` (integer) **[Optional]**: Number of results to return. Default is 10.

4. **range_search_tool**
   - **Description**: Performs a search with range filtering.
   - **Parameters**:
     - `index_name` (string) **[Required]**: Name of the Elasticsearch index.
     - `query` (object) **[Required]**: Key-value pairs to match documents.
     - `range_field` (string) **[Required]**: Field to apply range filter on.
     - `gte` (number) **[Optional]**: Greater than or equal value.
     - `lte` (number) **[Optional]**: Less than or equal value.
     - `size` (integer) **[Optional]**: Number of results to return. Default is 10.

5. **query_string_search_tool**
   - **Description**: Performs a search using Elasticsearch's query string syntax.
   - **Parameters**:
     - `index_name` (string) **[Required]**: Name of the Elasticsearch index.
     - `query_string` (string) **[Required]**: Query string in Elasticsearch syntax.
     - `size` (integer) **[Optional]**: Number of results to return. Default is 10.

6. **filtered_aggregation_tool**
   - **Description**: Performs an aggregation with filtering.
   - **Parameters**:
     - `index_name` (string) **[Required]**: Name of the Elasticsearch index.
     - `query` (object) **[Required]**: Key-value pairs for filtering documents.
     - `agg_field` (string) **[Required]**: Field to perform aggregation on.
     - `agg_type` (string) **[Optional]**: Type of aggregation (`sum`, `avg`, `min`, `max`, `count`). Default is `sum`.

7. **scroll_search_tool**
   - **Description**: Performs a scroll search for large datasets.
   - **Parameters**:
     - `index_name` (string) **[Required]**: Name of the Elasticsearch index.
     - `query` (object) **[Required]**: Key-value pairs to match documents.
     - `scroll_time` (string) **[Optional]**: Scroll context retention period (e.g., `"1m"` for 1 minute). Default is `"1m"`.
     - `size` (integer) **[Optional]**: Number of results per batch. Default is 100.

8. **bulk_index_tool**
   - **Description**: Bulk indexes a list of documents.
   - **Parameters**:
     - `index_name` (string) **[Required]**: Name of the Elasticsearch index.
     - `docs` (list of objects) **[Required]**: List of documents to index. Each document must include an `id` field.

9. **update_documents_by_query**
   - **Description**: Updates documents in the specified index based on a query.
   - **Parameters**:
     - `index_name` (string) **[Required]**: Name of the Elasticsearch index.
     - `query` (object) **[Required]**: Key-value pairs to match documents.
     - `script_source` (string) **[Required]**: Painless script defining the update operation.

10. **delete_by_query_tool**
    - **Description**: Deletes documents that match the query.
    - **Parameters**:
      - `index_name` (string) **[Required]**: Name of the Elasticsearch index.
      - `query` (object) **[Required]**: Key-value pairs to identify documents to delete.

11. **multi_index_search_tool**
    - **Description**: Searches across multiple indices.
    - **Parameters**:
      - `index_names` (list of strings) **[Required]**: List of Elasticsearch indices to search.
      - `query` (object) **[Required]**: Key-value pairs to match documents.
      - `size` (integer) **[Optional]**: Number of results to return. Default is 10.

12. **term_suggestion_tool**
    - **Description**: Provides term suggestions for autocomplete.
    - **Parameters**:
      - `index_name` (string) **[Required]**: Name of the Elasticsearch index.
      - `field` (string) **[Required]**: Field to provide suggestions for.
      - `term` (string) **[Required]**: Input term to base suggestions on.

13. **nested_query_tool**
    - **Description**: Searches within nested fields.
    - **Parameters**:
      - `index_name` (string) **[Required]**: Name of the Elasticsearch index.
      - `path` (string) **[Required]**: Path to the nested field.
      - `query` (object) **[Required]**: Key-value pairs to match within the nested field.
      - `size` (integer) **[Optional]**: Number of results to return. Default is 10.

14. **geo_location_search_tool**
    - **Description**: Searches for documents within a specific radius of a given geo-location.
    - **Parameters**:
      - `index_name` (string) **[Required]**: Name of the Elasticsearch index.
      - `location_field` (string) **[Required]**: Field containing geo-location data.
      - `lat` (number) **[Required]**: Latitude of the center point.
      - `lon` (number) **[Required]**: Longitude of the center point.
      - `distance` (string) **[Optional]**: Radius to search within (e.g., `"10km"`). Default is `"10km"`.
      - `size` (integer) **[Optional]**: Number of results to return. Default is 10.

15. **complex_aggregation_tool**
    - **Description**: Performs complex aggregations involving multiple fields and sub-aggregations.
    - **Parameters**:
      - `index_name` (string) **[Required]**: Name of the Elasticsearch index.
      - `aggs_body` (object) **[Required]**: Aggregation body as per Elasticsearch specifications.

### Instructions:

1. **Understand the User Query**: Analyze the user's input and determine the most appropriate tool from the list above to fulfill the request.

2. **Extract Necessary Parameters**:
   - Identify all required parameters for the chosen tool based on the user's request.
   - Include optional parameters if they are specified or implied in the user's query.
   - Ensure all parameter values are correctly inferred and formatted.

3. **Format the Response**:
   - Provide the response in **valid JSON format**.
   - Include all necessary parameters with correct data types.
   - Use the following structure:

```json
{
  "tool_name": "<tool_name>",
  "parameters": {
    "param1": "value1",
    "param2": ["value2a", "value2b"],
    "param3": 10,
    ...
  }
}
4. Ensure Correctness and Clarity:
    - Double-check that all parameters align with the tool's requirements.
    - If the user's intent is unclear, choose the tool that best fits the probable intent.
    - Do not include any additional explanations or text outside the JSON response.


Few-Shot Learning Examples:
Example 0:
User Query: "What is the balance of Account number 1863999845"
Llama 3.1 response:
{
  "tool_name": "basic_search_tool",
  "parameters": {
    "index_name": "banking_data",
    "query": {
      "account_number": "1863999845"
    },
    "fields": ["outstanding_balance"]
  }
}

Example 1:
User Query: "Find the average outstanding balance for all accounts in USD."
Llama 3.1 Response:
{
  "tool_name": "aggregation_tool",
  "parameters": {
    "index_name": "banking_data",
    "agg_field": "outstanding_balance",
    "agg_type": "avg",
    "query": {
      "currency_code": "USD"
    }
  }
}

Example 2:
User Query: "Search for all customers named 'John Doe' in the database."
Llama 3.1 Response:
{
  "tool_name": "basic_search_tool",
  "parameters": {
    "index_name": "banking_data",
    "query": {
      "customer_name": "John Doe"
    }
  }
}

Example 3:
User Query: "Find all accounts with a balance greater than 1 million PKR."
Llama 3.1 Response:
{
  "tool_name": "range_search_tool",
  "parameters": {
    "index_name": "banking_data",
    "range_field": "outstanding_balance",
    "gte": 1000000
  }
}

Example 4:
User Query: "Provide suggestions for customer names starting with 'Jon'."
Llama 3.1 Response:
{
  "tool_name": "term_suggestion_tool",
  "parameters": {
    "index_name": "banking_data",
    "field": "customer_name",
    "term": "Jon"
  }
}

Example 5:
User Query: "Update all 'Current' accounts to 'Closed' for accounts with zero balance."
Llama 3.1 Response:
{
  "tool_name": "update_documents_by_query",
  "parameters": {
    "index_name": "banking_data",
    "query": {
      "account_type_name": "Current",
      "outstanding_balance": 0
    },
    "script_source": "ctx._source.account_status = 'Closed'"
  }
}


Fields Available for Querying:
account_number (keyword)
customer_name (text)
outstanding_balance (float)
currency_code (keyword)
profession_code_description (text)
city_residential (text, keyword)
last_debit_transaction_date (date)
ac_found_ata_nacta (sc197) (boolean)
ac_remediation_req (sc195) (boolean)
account_closing (sc030) (boolean)
account_closing_date (date)
account_opening_date (date)
account_title (text)
account_type_code (keyword)
account_type_name (keyword)
address (text)
advise_all_debits (sc012) (boolean)
bio_verification (sc194) (boolean)
blocked_account (sc017) (boolean)
branch_code (keyword)
branch_name (text, keyword)
charges_deduction (sc 171) (boolean)
cif (keyword)
cnic (keyword)
cnic_corporate_customer (keyword)
contact_number (keyword)
currency_name (keyword)
customer_type_code (keyword)
customer_type_description (text, keyword)
date_of_birth (date)
email (keyword)
father_name (text, keyword)
financial_supporter_cnic (keyword)
financial_supporter_father_name (text, keyword)
financial_supporter_name (text, keyword)
financial_supporter_nationality (keyword)
first_activation_date (date)
frozen_govt_order (sc166) (boolean)
inactive_account (sc020) (boolean)
introducer_cnic (keyword)
introducer_name (text, keyword)
joint1 (text, keyword)
kyc_brief_comments (text)
last_12_months_credit_transaction (integer)
last_12_months_debit_transaction (integer)
last_activation_date (date)
last_debit_transaction_amount (float)
locker_holder (sc080) (boolean)
mandate_holder_mobile_number (keyword)
mandate_holder_name (text, keyword)
name_of_cnic_holders_corporate_customer (text, keyword)
nationality (keyword)
ntn (keyword)
pep (boolean)
profession_code (keyword)
region_code (keyword)
region_name (text, keyword)
registration_number (keyword)
risk_category_code (keyword)
risk_category_description (text, keyword)
role_of_cnic_corporate_customer (text, keyword)
spouse_name (text, keyword)
suffix (text)
unclaimed_account (sc010) (boolean)

Please identify the appropriate tool and specify the correct field and value to execute the following user query.




"""

def process_query_with_llama(user_query):
    prompt = prompt_template + f"\nUser Query: {user_query}"
    result = subprocess.run(['ollama', 'run', 'llama3.1'], input=prompt, text=True, capture_output=True)
    return result.stdout.strip()



def parse_response(response):
    """
    Dynamically parse the response from the LLM to determine the tool to use and the parameters.
    """
    # Initialize empty variables for tool, query, fields, and additional parameters
    tool_name = None
    query_dict = {}
    fields = []
    additional_params = {}

    # Detect the tool to be used
    tool_match = re.search(r'"tool_name"\s*:\s*"(\w+)"', response, re.IGNORECASE)
    if tool_match:
        tool_name = tool_match.group(1)

    # Extract query parameters (e.g., field: value pairs)
    query_match = re.search(r'"query"\s*:\s*{([^}]+)}', response, re.IGNORECASE)
    if query_match:
        query_pairs = re.findall(r'"(\w+)"\s*:\s*"([^"]+)"', query_match.group(1))
        query_dict = {field: value for field, value in query_pairs}

    # Extract fields (if specified)
    fields_match = re.search(r'"fields"\s*:\s*\[([^\]]+)\]', response, re.IGNORECASE)
    if fields_match:
        fields = [field.strip().strip('"') for field in fields_match.group(1).split(",")]

    # Extract additional parameters such as agg_field, agg_type, etc.
    agg_field_match = re.search(r'"agg_field"\s*:\s*"([^"]+)"', response, re.IGNORECASE)
    if agg_field_match:
        additional_params['agg_field'] = agg_field_match.group(1)

    agg_type_match = re.search(r'"agg_type"\s*:\s*"([^"]+)"', response, re.IGNORECASE)
    if agg_type_match:
        additional_params['agg_type'] = agg_type_match.group(1)

    # Add more parameter extraction as needed for other tools

    return tool_name, {"query": query_dict, "fields": fields, **additional_params}


def handle_query(user_query):
    try:
        response = process_query_with_llama(user_query)
        print(response)

        # Parse the response to determine the appropriate tool and parameters
        tool, params = parse_response(response)
        print("Tool: ", tool)
        print("Parameters: ", params)

        # Execute the corresponding tool with the parsed parameters
        if tool == "basic_search_tool":
            index_name = "banking_data"  # Assuming the index is banking_data
            query_dict = params.get('query', {})
            fields = params.get('fields', None)  # Get fields if specified by the model
            result = basic_search_tool(index_name, query_dict, fields=fields)
        elif tool == "aggregation_tool":
            index_name = "banking_data"
            agg_field = params.get('agg_field')
            agg_type = params.get('agg_type', 'sum')  # Default to 'sum' if not specified
            result = aggregation_tool(index_name, agg_field, agg_type)
        elif tool == "multi_match_search_tool":
            index_name = "banking_data"
            search_term = params.get('search_term')
            fields = params.get('fields', [])
            result = multi_match_search_tool(index_name, search_term, fields)
        elif tool == "range_search_tool":
            index_name = "banking_data"
            query_dict = params.get('query', {})
            range_field = params.get('range_field')
            gte = params.get('gte')
            lte = params.get('lte')
            result = range_search_tool(index_name, query_dict, range_field, gte=gte, lte=lte)
        elif tool == "query_string_search_tool":
            index_name = "banking_data"
            query_string = params.get('query_string')
            result = query_string_search_tool(index_name, query_string)
        elif tool == "filtered_aggregation_tool":
            index_name = "banking_data"
            query_dict = params.get('query', {})
            agg_field = params.get('agg_field')
            agg_type = params.get('agg_type')
            result = filtered_aggregation_tool(index_name, query_dict, agg_field, agg_type)
        elif tool == "scroll_search_tool":
            index_name = "banking_data"
            query_dict = params.get('query', {})
            result = scroll_search_tool(index_name, query_dict)
        elif tool == "bulk_index_tool":
            index_name = "banking_data"
            docs = params.get('docs', [])
            result = bulk_index_tool(index_name, docs)
        elif tool == "update_documents_by_query":
            index_name = "banking_data"
            query_dict = params.get('query', {})
            script_source = params.get('script_source')
            result = update_documents_by_query(index_name, query_dict, script_source)
        elif tool == "delete_by_query_tool":
            index_name = "banking_data"
            query_dict = params.get('query', {})
            result = delete_by_query_tool(index_name, query_dict)
        elif tool == "term_suggestion_tool":
            index_name = "banking_data"
            field = params.get('field')
            term = params.get('term')
            result = term_suggestion_tool(index_name, field, term)
        elif tool == "nested_query_tool":
            index_name = "banking_data"
            path = params.get('path')
            query_dict = params.get('query', {})
            result = nested_query_tool(index_name, path, query_dict)
        elif tool == "geo_location_search_tool":
            index_name = "banking_data"
            location_field = params.get('location_field')
            lat = params.get('lat')
            lon = params.get('lon')
            distance = params.get('distance')
            result = geo_location_search_tool(index_name, location_field, lat, lon, distance)
        elif tool == "complex_aggregation_tool":
            index_name = "banking_data"
            aggs_body = params.get('aggs_body')
            result = complex_aggregation_tool(index_name, aggs_body)
        else:
            return f"Unrecognized tool or no valid tool matched: {response}"

        return result

    except Exception as e:
        return f"Error handling query: {str(e)}"


app = Flask(__name__)

# Your backend functions like `handle_query`, `parse_response`, etc., should be defined here.

@app.route('/')
def index():
    return render_template('index.html')

def generate_html_table(data):
    if not data:
        return "No data available."

    table_html = "<table style='width:100%;border:1px solid black;'>"
    table_html += "<tr>"

    # Assuming the first item has the structure you need
    first_item = data[0]['_source']
    headers = first_item.keys()

    # Add table headers
    for header in headers:
        table_html += f"<th style='border:1px solid black;padding:8px;background-color:#f2f2f2;'>{header}</th>"
    table_html += "</tr>"

    # Add table rows
    for item in data:
        table_html += "<tr>"
        for header in headers:
            table_html += f"<td style='border:1px solid black;padding:8px;'>{item['_source'][header]}</td>"
        table_html += "</tr>"

    table_html += "</table>"
    return table_html


@app.route('/get_response', methods=['POST'])
def get_response():
    try:
        user_message = request.json['message']
        # Process the user message and get the response
        response_data = handle_query(user_message)  # Assuming handle_query is your processing function
        return jsonify(response_data)
    except KeyError as e:
        return jsonify({"error": f"Missing data: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": "An error occurred during processing"}), 500

if __name__ == "__main__":
    app.run(debug=True)
