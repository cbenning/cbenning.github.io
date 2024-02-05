---
layout: post
title: Automatic Serialization with Celery and Pydantic Models
categories: [fastapi, celery, python, pydantic, serialization]
tags: [fastapi, celery, python, pydantic, serialization]
status: publish
type: post
published: true
comments: true
meta:
  _edit_last: '1'

---

# Automatic Serialization with Celery and Pydantic Models

I'm working on a project involving FastApi (which uses Pydantic models under the hood) and Celery. I wanted to have a nice clean way to pass Pydantic models to Celery tasks so I could avoid translating back and forth. To my surprise this doesn't work natively, though it does seem like [it has been considered](https://github.com/celery/celery/issues/8751)
 
I ended up solving this using Celery's ability to add custom serializers and [this helpful starting example](https://stackoverflow.com/questions/21631878/celery-is-there-a-way-to-write-custom-json-encoder-decoder).

### Structure

```
main.py
models/
  __init__.py
  models.py
pydanticserializer/
  __init__.py
  pydanticserializer.py
```


### models.py

Create a module around this 

```python

from pydantic import BaseModel

class MyCustomTypeOne(BaseModel):
  myfield:str

class MyCustomTypeTwo(BaseModel):
  myotherfield:str

```

### pydanticserializer.py
```python

import json
from pydantic import BaseModel
import models

class PydanticSerializer(json.JSONEncoder):   
    def default(self, obj):
        if isinstance(obj, BaseModel):
            return obj.model_dump() | {'__type__': type(obj).__name__}
        else:
            return json.JSONEncoder.default(self, obj)

def pydantic_decoder(obj):
    if '__type__' in obj:
        if obj['__type__'] in dir(models):
            cls = getattr(models, obj['__type__'])
            return cls.parse_obj(obj)
    return obj


# Encoder function      
def pydantic_dumps(obj):
    return json.dumps(obj, cls=PydanticSerializer)

# Decoder function
def pydantic_loads(obj):
    return json.loads(obj, object_hook=pydantic_decoder)
```

### main.py

```python
from celery import Celery
from kombu.serialization import register
import pydanticserializer

# Register new serializer methods into kombu
register(
    "pydantic",
    pydanticserializer.pydantic_dumps,
    pydanticserializer.pydantic_loads,
    content_type="application/x-pydantic",
    content_encoding="utf-8",
)

celery_app = Celery()

celery_app.conf.update(
    task_serializer="pydantic",
    result_serializer="pydantic",
    event_serializer="pydantic",
    accept_content=["application/json", "application/x-pydantic"],
    result_accept_content=["application/json", "application/x-pydantic"],
)

```

So now that that is wired up you should be able to setup tasks that accept and return these models natively

```python
@celery_app.task(bind=True)
def mytask(self, req: MyCustomTypeOne) -> MyCustomTypeOne:
  ...
  return MyCustomTypeTwo(myotherfield="...")

```

...As well as invoke them in this way

```python

req = MyCustomTypeOne(myfield="...")
async_result = mytask.delay(input)
...
result: MyCustomTypeTwo = async_result.get()

```