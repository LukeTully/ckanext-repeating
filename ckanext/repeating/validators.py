import json
import re
from ckan.plugins.toolkit import missing, _

def repeating_text(key, data, errors, context):
    """
    Accept repeating text input in the following forms
    and convert to a json list for storage:

    1. a list of strings, eg.

       ["Person One", "Person Two"]

    2. a single string value to allow single text fields to be
       migrated to repeating text

       "Person One"

    3. separate fields per language (for form submissions):

       fieldname-0 = "Person One"
       fieldname-1 = "Person Two"
    """

    # just in case there was an error before our validator,
    # bail out here because our errors won't be useful
    if errors[key]:
        return

    value = data[key]
    # 1. list of strings or 2. single string
    if value is not missing:
        if isinstance(value, basestring):
            value = [value]
        if not isinstance(value, list):
            errors[key].append(_('expecting list of strings'))
            return

        out = []
        for element in value:
            if not isinstance(element, basestring):
                errors[key].append(_('invalid type for repeating text: %r')
                    % element)
                continue
            if isinstance(element, str):
                try:
                    element = element.decode('utf-8')
                except UnicodeDecodeError:
                    errors[key]. append(_('invalid encoding for "%s" value')
                        % lang)
                    continue
            out.append(element)

        if not errors[key]:
            data[key] = json.dumps(out)
        return

    # 3. separate fields
    found = {}
    prefix = key[-1] + '['
    extras = data.get(key[:-1] + ('__extras',), {})

    to_remove = []
    for name, text in extras.iteritems():
        if not name.startswith(prefix):
            continue
        if not text:
            continue
        to_remove.append(name)
        matches = re.findall(re.escape(prefix) + r"(\d*)\]\[(\w*)\]", name)
        index = matches[0][0]
        prop = matches[0][1]
        try:
            index = int(index)
        except ValueError:
            continue
        try: 
            found[index][prop] = text
        except KeyError:
            found[index] = {}
            found[index][prop] = text
            
    for extra in to_remove:
        data.get(key[:-1] + ('__extras',), {}).pop(extra)
        if ('__junk',) in data:
            data.get(('__junk',)).pop(extra)
            # TODO: Check to make sure this is the right key that I'm popping
            # Also double check that there isn't a pre-existing mechanism for handling extras detritis
    out = [found[i] for i in sorted(found)]
    data[key] = json.dumps(out)


def repeating_text_output(value):
    """
    Return stored json representation as a list, if
    value is already a list just pass it through.
    """
    if isinstance(value, list):
        return value
    if value is None:
        return []
    try:
        return json.loads(value)
    except ValueError:
        return [value]
