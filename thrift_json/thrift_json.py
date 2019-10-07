#!/usr/bin/env python3

# Modified from
#MIT License
#Copyright (c) 2016, Young King
#Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# Additional changes by Charter Chapman
# works with python3
# Seems to work with thrift in 2019

import json
from thrift.Thrift import TType
from thrift.protocol import TJSONProtocol
from thrift.transport import TTransport

class ThriftJSONEncoder(json.JSONEncoder):

    def default(self, o):
        if not hasattr(o, 'thrift_spec'):
            return super(ThriftJSONEncoder, self).default(o)

        spec = getattr(o, 'thrift_spec')
        ret = {}
        for field in spec:
            if field is None:
                continue
            (tag, field_ttype, field_name, field_ttype_info, default) = field
            if field_name in o.__dict__:
                val = o.__dict__[field_name]
                if val != default:
                    ret[field_name] = val
        return ret


def thrift2json(obj):
    return json.dumps(obj, cls=ThriftJSONEncoder)


def thrift2dict(obj):
    str = thrift2json(obj)
    return json.loads(str)


def prettyjson2TJSON(json_str, thrift_class):
    obj = json2thrift(json_str, thrift_class)
    # obj = json.loads(, cls=ThriftJSONDecoder, thrift_class=thrift_class)

    protocol_factory = TJSONProtocol.TJSONProtocolFactory()

    trans = TTransport.TMemoryBuffer()
    prot = protocol_factory.getProtocol(trans)
    obj.write(prot)

    tjson = trans.getvalue()
    return tjson


class ThriftJSONDecoder(json.JSONDecoder):

    def __init__(self, *args, **kwargs):
        self._thrift_class = kwargs.pop('thrift_class')
        super(ThriftJSONDecoder, self).__init__(*args, **kwargs)

    def decode(self, json_str):
        if isinstance(json_str, dict):
            dct = json_str
        else:
            dct = super(ThriftJSONDecoder, self).decode(json_str)
        return self._convert(dct, TType.STRUCT,
                             (self._thrift_class, self._thrift_class.thrift_spec))

    def _convert(self, val, ttype, ttype_info):
        if ttype == TType.STRUCT:
            (thrift_class, thrift_spec) = ttype_info
            ret = thrift_class()
            for field in thrift_spec:
                if field is None:
                    continue
                (tag, field_ttype, field_name, field_ttype_info, dummy) = field
                if field_name not in val:
                    continue
                converted_val = self._convert(val[field_name], field_ttype, field_ttype_info)
                setattr(ret, field_name, converted_val)
        elif ttype == TType.LIST:
            (element_ttype, element_ttype_info, dummy) = ttype_info

            ret = [self._convert(x, element_ttype, element_ttype_info) for x in val]
        elif ttype == TType.SET:
            (element_ttype, element_ttype_info) = ttype_info
            ret = set([self._convert(x, element_ttype, element_ttype_info) for x in val])
        elif ttype == TType.MAP:
            print(len(ttype_info))
            (key_ttype, key_ttype_info, val_ttype, val_ttype_info, some_bool_dummy) = ttype_info
            ret = dict([(self._convert(k, key_ttype, key_ttype_info),
                         self._convert(v, val_ttype, val_ttype_info)) for (k, v) in val.items()])
        elif ttype == TType.STRING:
            #print(type(val))
            if isinstance(val, str):
                ret = val
            else:
                #ret = str.encode(val)
                ret = val
        elif ttype == TType.DOUBLE:
            ret = float(val)
        elif ttype == TType.I64 or ttype == TType.I32 or ttype == TType.I16 or ttype == TType.BYTE:
            ret = int(val)
        elif ttype == TType.BOOL:
            ret = bool(val)
        else:
            raise TypeError('Unrecognized thrift field type: %d' % ttype)
        return ret


def json2thrift(json_str, thrift_class):
    return json.loads(json_str, cls=ThriftJSONDecoder, thrift_class=thrift_class)

def loadjson2thrift(path, thrift_class):
        # load program def for this test
    with open(path, encoding='utf-8') as data_file:
        p_json = json.loads(data_file.read())

    return json2thrift(json.dumps(p_json), thrift_class)

def loadjson(path):
    with open(path, encoding='utf-8') as data_file:
        return json.loads(data_file.read())
