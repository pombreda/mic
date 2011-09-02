#!/usr/bin/python -tt
#
# Copyright 2011 Intel, Inc.
#
# This copyrighted material is made available to anyone wishing to use, modify,
# copy, or redistribute it subject to the terms and conditions of the GNU
# General Public License v.2.  This program is distributed in the hope that it
# will be useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.  Any Red Hat
# trademarks that are incorporated in the source code or documentation are not
# subject to the GNU General Public License and may only be used or replicated
# with the express permission of Red Hat, Inc.
#

from mic import configmgr, pluginmgr, chroot, msger
from mic.utils import cmdln, errors
from mic.imager import fs

from mic.pluginbase import ImagerPlugin
class FsPlugin(ImagerPlugin):
    name = 'fs'

    @classmethod
    @cmdln.option("--include-src", dest="include_src", help="include source pakcage")
    def do_create(self, subcmd, opts, *args):
        """${cmd_name}: create fs image

        ${cmd_usage}
        ${cmd_option_list}
        """

        if not args:
            raise errors.Usage("More arguments needed")

        if len(args) == 1:
            ksconf = args[0]
        else:
            raise errors.Usage("Extra arguments given")

        cfgmgr = configmgr.getConfigMgr()
        createopts = cfgmgr.create
        cfgmgr.setProperty("ksconf", ksconf)

        # try to find the pkgmgr
        pkgmgr = None
        plgmgr = pluginmgr.PluginMgr()
        for (key, pcls) in plgmgr.get_plugins('backend').iteritems():
            if key == createopts['pkgmgr']:
                pkgmgr = pcls
                break

        if not pkgmgr:
            raise CreatorError("Can't find backend plugin: %s" % createopts['pkgmgr'])

        creator = fs.FsImageCreator(createopts, pkgmgr)
        try:
            creator.check_depend_tools()
            creator.mount(None, createopts["cachedir"])
            creator.install()
            #Download the source packages ###private options
            if opts.include_src:
                installed_pkgs =  creator.get_installed_packages()
                msger.info('--------------------------------------------------')
                msger.info('Generating the image with source rpms included, The number of source packages is %d.' %(len(installed_pkgs)))
                if not misc.SrcpkgsDownload(installed_pkgs, createopts["repomd"], creator._instroot, createopts["cachedir"]):
                    msger.warning("Source packages can't be downloaded")

            creator.configure(createopts["repomd"])
            creator.unmount()
            creator.package(createopts["outdir"])
            outimage = creator.outimage
            creator.print_outimage_info()
        except errors.CreatorError, e:
            raise
        finally:
            creator.cleanup()

        msger.info("Finished.")
        return 0

    @classmethod
    def do_chroot(self, target):#chroot.py parse opts&args
            try:
                chroot.chroot(target, None, "/bin/env HOME=/root /bin/bash")
            except:
                msger.warning("Failed to chroot to %s." % target)
            finally:
                chroot.cleanup_after_chroot("dir", None, None, None)
                return 1

