#!/usr/bin/env python
#
# Citizen Desk
#

import datetime

try:
    unicode
except:
    unicode = str

from citizendesk.feeds.sms.report.storage import collection, schema, FEED_TYPE, PUBLISHER_TYPE
from citizendesk.common.utils import get_id_value as _get_id_value
from citizendesk.common.utils import get_boolean as _get_boolean
from citizendesk.common.utils import get_sort as _get_sort

DEFAULT_LIMIT = 20

'''
Here we should list (saved) reports filtered according to _id of saved sms-based reports.
'''

def do_get_one(db, doc_id):
    '''
    returns data of a single citizen alias
    '''
    if not db:
        return (False, 'inner application error')

    coll = db[collection]

    doc_id = _get_id_value(doc_id)

    spec = {'_id': doc_id, 'feed_type': FEED_TYPE}
    doc = coll.find_one(spec)

    if not doc:
        return (False, 'report not found')

    return (True, doc)

def do_get_list(db, spec_type, spec_id, offset=None, limit=None, sort=None, other=None):
    '''
    returns data of a set of sms citizen aliases
    '''
    if not db:
        return (False, 'inner application error')

    list_spec = {'feed_type': FEED_TYPE}
    if 'session_id' == spec_type:
        list_spec['session'] = spec_id
    if 'sent_to' == spec_type:
        list_spec['recipients.identifiers'] = {'type':'phone_number', 'value':spec_id}
    if 'received_from' == spec_type:
        list_spec['authors.identifiers'] = {'type':'phone_number', 'value':spec_id}

    sort_list = _get_sort(sort)
    if not sort_list:
        sort_list = [('produced', 1)]

    text_only = False
    if other and ('text_only' in other) and other['text_only']:
        try:
            text_only = bool(_get_boolean(other['text_only']))
        except:
            text_only = False

    coll = db[collection]
    cursor = coll.find(list_spec).sort(sort_list)

    total = cursor.count()

    if limit is None:
        limit = DEFAULT_LIMIT

    if offset:
        cursor = cursor.skip(offset)
    if limit:
        cursor = cursor.limit(limit)

    docs = []
    for entry in cursor:
        if not entry:
            continue
        if not text_only:
            docs.append(entry)
        else:
            one_text = {
                'original': None,
                'authors': None,
                'recipients': None
            }
            authors = []
            recipients = []
            if 'original' in entry:
                one_text['original'] = entry['original']
            if ('authors' in entry) and (type(entry['authors']) in (list, tuple)):
                for one_author in entry['authors']:
                    if (type(one_author) is dict) and ('identifiers' in one_author) and (one_author['identifiers']):
                        one_alias_set = one_author['identifiers']
                        if (type(one_alias_set) in (list, tuple)):
                            for one_alias in one_alias_set:
                                if (type(one_alias) is dict) and ('value' in one_alias) and (one_alias['value']):
                                    authors.append(one_alias['value'])
            if ('recipients' in entry) and (type(entry['recipients']) in (list, tuple)):
                for one_recipient in entry['recipients']:
                    if (type(one_recipient) is dict) and ('identifiers' in one_recipient) and (one_recipient['identifiers']):
                        one_alias_set = one_recipient['identifiers']
                        if (type(one_alias_set) in (list, tuple)):
                            for one_alias in one_alias_set:
                                if (type(one_alias) is dict) and ('value' in one_alias) and (one_alias['value']):
                                    recipients.append(one_alias['value'])
            if authors:
                try:
                    one_text['authors'] = ', '.join(authors)
                except:
                    pass
            if recipients:
                try:
                    one_text['recipients'] = ', '.join(recipients)
                except:
                    pass
            if (not one_text['original']) and (not one_text['authors']) and (not one_text['recipients']):
                continue

            docs.append(one_text)

    return (True, docs, {'total': total})
