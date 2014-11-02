'''chromium apport hook

/usr/share/apport/package-hooks/chromium-browser.py

Copyright (c) 2010, Fabien Tassin <fta@sofaraway.org>
Copyright (c) 2014, Canonical

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation; either version 2 of the License, or (at your
option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
the full text of the license.
'''

# pylint: disable=line-too-long, missing-docstring, invalid-name

from __future__ import print_function
import os, sys, getopt, codecs
import time
import apport.hookutils
import subprocess
import json

HOME = os.getenv("HOME")
PACKAGE = 'chromium-browser'
RELATED_PACKAGES = [
    PACKAGE,
    'chromium-browser-l10n',
    'chromium-browser-inspector',
    'chromium-browser-dbg',
    'chromium-codecs-ffmpeg',
    'chromium-codecs-ffmpeg-extra',
    'libvpx0',
    'libgtk2.0-0',
    'nspluginwrapper',
    # various plugins
    'chromiumflashplugin',
    'pepperflashplugin-nonfree',
    'pepflashplugin-nonfree',
    'flashplugin-installer',
    'rhythmbox-plugins',
    'totem-mozilla',
    'icedtea6-plugin',
    'moonlight-plugin-chromium',
    'sun-java6-bin',
    'acroread',
    'google-talkplugin',
    # chrome
    'google-chrome-unstable',
    'google-chrome-beta',
    'google-chrome-stable',
]

def installed_version(report, pkgs):
    report['RelatedPackagesPolicy'] = ''
    for pkg in pkgs:
        script = subprocess.Popen(['apt-cache', 'policy', pkg], stdout=subprocess.PIPE)
        report['RelatedPackagesPolicy'] += str(script.communicate()[0]) + "\n"

def gconf_values(report, keys):
    report['gconf-keys'] = ''
    for key in keys:
        try:
            script = subprocess.Popen(['gconftool-2', '--get', key], stdout=subprocess.PIPE)
        except OSError:
            report['gconf-keys'] = "gconftool-2 not found"
            return
        out = str(script.communicate()[0])
        if out == "":
            out = "**unset**\n"
        report['gconf-keys'] += key + " = " + out

def get_user_profile_dir():
    profiledir = HOME + "/.config/chromium/Default"
    # see if report['ProcCmdline'] contains a --user-data-dir=xxx and use it if it still exists
    return profiledir

def user_prefs(report, filename):
    with open(filename, 'r') as f:
        entry = json.load(f)
    report['ChromiumPrefs'] = ''

    if 'browser' in entry and 'check_default_browser' in entry['browser']:
        report['ChromiumPrefs'] += "browser/check_default_browser = " + \
            str(entry['browser']['check_default_browser']) + "\n"
    else:
        report['ChromiumPrefs'] += "browser/check_default_browser = **unset** (no such key yet)\n"

    if 'theme' in entry['extensions']:
        if 'use_system' in entry['extensions']['theme']:
            report['ChromiumPrefs'] += "extensions/theme/use_system = " + \
                  str(entry['extensions']['theme']['use_system']) + "\n"
        else:
            report['ChromiumPrefs'] += "extensions/theme/use_system = **unset** (no such key)\n"

    # list entensions+versions
    report['ChromiumPrefs'] += "extensions/settings =\n"
    if 'settings' in entry['extensions']:
        for ext in list(entry['extensions']['settings'].keys()):
            report['ChromiumPrefs'] += " - '" + ext + "'\n"
            if 'manifest' in entry['extensions']['settings'][ext]:
                for k in ['name', 'description', 'version', 'update_url']:
                    report['ChromiumPrefs'] += "     manifest/%s = %s\n" % (k, "'" + entry['extensions']['settings'][ext]['manifest'][k] + "'" if k in entry['extensions']['settings'][ext]['manifest'] else "*undef*")
            else:
                report['ChromiumPrefs'] += "     manifest/* = *undef*\n"
            for k in ['blacklist', 'state']:
                if k in entry['extensions']['settings'][ext]:
                    report['ChromiumPrefs'] += "     %s = %s\n" % (k, repr(entry['extensions']['settings'][ext][k]))
    else:
        report['ChromiumPrefs'] += " (no entry found in the Preferences file)"

    # list plugins
    # (for some reason, this key is not populated until something is (manually?)
    #  changed in about:plugins)
    report['DetectedPlugins'] = ""
    if 'plugins' in entry and 'plugins_list' in entry['plugins']:
        for plugin in entry['plugins']['plugins_list']:
            report['DetectedPlugins'] += "=> " + plugin['name'] + "\n" + \
                "   - enabled = " + str(plugin['enabled']) + "\n"
            if 'path' in plugin:
                report['DetectedPlugins'] += "   - path    = " + plugin['path'] + "\n"
    else:
        report['DetectedPlugins'] += "(no entry found in the Preferences file)"

def list_installed_plugins(report):
    # $SRC/webkit/glue/plugins/plugin_list_posix.cc
    # 1/ MOZ_PLUGIN_PATH env variable
    # 2/ ~/.mozilla/plugins
    # 3/ /usr/lib/browser-plugins /usr/lib/mozilla/plugins /usr/lib/firefox/plugins
    #    /usr/lib/xulrunner-addons/plugins
    # and on x64 systems (unless /usr/lib64 is a symlink to /usr/lib):
    #    /usr/lib64/browser-plugins /usr/lib64/mozilla/plugins /usr/lib64/firefox/plugins
    #    /usr/lib64/xulrunner-addons/plugins
    # It's not clear if $SRC/third_party/WebKit/WebCore/plugins/PluginDatabase.cpp
    # is also used (if it is, we need the zillions dirs from PluginDatabase::defaultPluginDirectories()
    report['InstalledPlugins'] = ''
    dirs = {}

    for plugindir in (HOME + "/.mozilla/plugins", "/usr/lib/browser-plugins", "/usr/lib/mozilla/plugins", "/usr/lib/firefox/plugins", "/usr/lib/xulrunner-addons/plugins", "/usr/lib64/browser-plugins", "/usr/lib64/mozilla/plugins", "/usr/lib64/firefox/plugins", "/usr/lib64/xulrunner-addons/plugins"):
        if os.path.exists(plugindir):
            d = os.path.realpath(plugindir)
            if d not in dirs:
                dirs[d] = True
                report['InstalledPlugins'] += plugindir + ":\n"
                for ent in os.listdir(d):
                    filename = os.path.join(d, ent)
                    report['InstalledPlugins'] += "  => " + ent  + "\n"
                    while os.path.islink(filename):
                        filename2 = os.readlink(filename)
                        if filename2 == filename:
                            report['InstalledPlugins'] += "     - (symlink loop, abort)\n"
                            break
                        if not os.path.exists(filename):
                            report['InstalledPlugins'] += "     - broken symlink to " + filename2 + "\n"
                            break
                        filename = os.path.normpath(os.path.join(os.path.dirname(filename), filename2))
                        report['InstalledPlugins'] += "     - symlink to " + filename + "\n"
                    if os.path.exists(filename):
                        st = os.stat(filename)
                        report['InstalledPlugins'] += "        (size: " + \
                            str(st.st_size) + " bytes, mtime: " + time.ctime(st.st_mtime) + ")\n"
                report['InstalledPlugins'] += "\n"

def get_envs(envs):
    return "\n".join(os.getenv(envs)) + "\n"

def add_info(report, userdir=None):
    apport.hookutils.attach_related_packages(report, RELATED_PACKAGES)
    installed_version(report, RELATED_PACKAGES)

    # Allow reports from PPAs
    if not apport.packaging.is_distro_package(PACKAGE):
        report['ThirdParty'] = 'True'
        report['CrashDB'] = 'ubuntu'

    for filename in os.listdir('/etc/chromium-browser/customizations'):
        try:
            with open(os.path.join('/etc/chromium-browser/customizations', filename)) as f:
                report['etcconfig/c/'+filename] = "\n".join(f.readlines())
        except IOError:
            report['etcconfig/c/'+filename] = "# could not read"

    try:
        with open('/etc/chromium-browser/default') as f:
            report['etcconfig/default'] = "\n".join(f.readlines())
    except IOError:
        report['etcconfig/default'] = "# could not read"

    try:
        report['user-desktop-file'] = \
          open(HOME + '/.local/share/applications/' + PACKAGE + '.desktop').read()
    except IOError:
        pass

    gconf_values(report, ['/desktop/gnome/applications/browser/exec', '/desktop/gnome/url-handlers/https/command', '/desktop/gnome/url-handlers/https/enabled', '/desktop/gnome/url-handlers/http/command', '/desktop/gnome/url-handlers/http/enabled', '/desktop/gnome/session/required_components/windowmanager', '/apps/metacity/general/compositing_manager', '/desktop/gnome/interface/icon_theme', '/desktop/gnome/interface/gtk_theme'])
    user_dir = userdir if userdir is not None else get_user_profile_dir()
    user_prefs(report, user_dir + "/Preferences")

    list_installed_plugins(report)

    # DE
    report['Desktop-Session'] = get_envs(['DESKTOP_SESSION', 'XDG_CONFIG_DIRS', 'XDG_DATA_DIRS'])

    # Env
    report['Env'] = get_envs(['MOZ_PLUGIN_PATH', 'LD_LIBRARY_PATH'])

    # Disk usage
    script = subprocess.Popen(['df', '-Th'], stdout=subprocess.PIPE)
    report['DiskUsage'] = str(script.communicate()[0]) + "\n\nInodes:\n"
    script = subprocess.Popen(['df', '-ih'], stdout=subprocess.PIPE)
    report['DiskUsage'] += str(script.communicate()[0])
    script = subprocess.Popen(['dmesg', '-k'], stdout=subprocess.PIPE)
    kernel_messages = list()
    for line in str(script.communicate()[0]).split("\n"):  # to str. Size bounded by dmesg buffer.
        if "chrom" in line.lower():
            kernel_messages.append(line + "\n")
    if kernel_messages:
        report['DmesgChromium'] = "".join(kernel_messages)

## DEBUGING ##
def main():
    sys.stdout = codecs.getwriter('utf8')(sys.stdout)
    try:
        opts, _ = getopt.getopt(sys.argv[1:], "-u:", ['user-dir='])
    except getopt.GetoptError as err:
        print(str(err))
        sys.exit(2)

    userdir = None
    for o, a in opts:
        if o in ("-u", "--user-dir"):
            userdir = a
        else:
            assert False, "unhandled option"

    report = {}
    add_info(report, userdir=userdir)
    for key in report:
        print('[%s]\n%s\n' % (key, report[key]))

if __name__ == '__main__':
    main()
