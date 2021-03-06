from django.http import HttpResponse, HttpRequest, HttpResponseRedirect
from django.template import RequestContext, Template, Context
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse
from django.http import Http404
#from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.conf import settings
from django import forms
from django.db.models import Q
from django.db.models import Count
from server import utils
from django.shortcuts import render_to_response, get_object_or_404, redirect
import plistlib
import hashlib

from models import *
from server.models import *

# Create your views here.

def decode_to_string(base64bz2data):
    '''Decodes an inventory submission, which is a plist-encoded
    list, compressed via bz2 and base64 encoded.'''
    try:
        bz2data = base64.b64decode(base64bz2data)
        return bz2.decompress(bz2data)
    except Exception:
        return ''

@csrf_exempt
def submit_catalog(request):
    if request.method != 'POST':
        raise Http404

    submission = request.POST
    key = submission.get('key')
    name = submission.get('name')
    machine_group = None
    if key:
        try:
            machine_group = MachineGroup.objects.get(key=key)
        except MachineGroup.DoesNotExist:
            raise Http404

        compressed_catalog = submission.get('base64bz2catalog')
        if compressed_catalog:
            compressed_catalog = compressed_catalog.replace(" ", "+")
            catalog_str = decode_to_string(compressed_catalog)

            try:
                catalog_plist = plistlib.readPlistFromString(catalog_str)
            except Exception:
                catalog_plist = None
            if catalog_plist:
                try:
                    catalog = Catalog.objects.get(name=name, machine_group=machine_group)
                except Catalog.DoesNotExist:
                    catalog = Catalog(name=name, machine_group=machine_group)
                catalog.sha256hash = \
                    hashlib.sha256(catalog_str).hexdigest()
                catalog.content = catalog_str
                catalog.save()
    return HttpResponse("Catalogs submitted.")
@csrf_exempt
def catalog_hash(request):
    if request.method != 'POST':
        print 'method not post'
        raise Http404

    output = []
    submission = request.POST
    key = submission.get('key')
    catalogs = submission.get('catalogs')
    if key:
        try:
            machine_group = MachineGroup.objects.get(key=key)
        except MachineGroup.DoesNotExist:
            raise Http404
    if catalogs:
        catalogs = catalogs.replace(" ", "+")
        catalogs = decode_to_string(catalogs)
        try:
            catalogs_plist = plistlib.readPlistFromString(catalogs)
        except Exception:
            catalogs_plist = None
        for item in catalogs_plist:
            name = item['name']
            sha256hash = item['sha256hash']
            try:
                found_catalog = Catalog.objects.get(name=name, machine_group=machine_group)
                output.append({'name': name, 'sha256hash':found_catalog.sha256hash})
            except Catalog.DoesNotExist:
                output.append({'name': name, 'sha256hash': ''})

    return HttpResponse(plistlib.writePlistToString(output))
