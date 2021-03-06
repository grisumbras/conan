import os
import textwrap
import unittest

from parameterized.parameterized import parameterized

from conans.client.tools.files import replace_in_file
from conans.test.utils.tools import TestClient, TestServer, GenConanfile


class ConanAliasTest(unittest.TestCase):

    def alias_overriden_test(self):
        # https://github.com/conan-io/conan/issues/3353
        client = TestClient()

        client.save({"conanfile.py": GenConanfile()})
        client.run("export . PkgA/0.1@user/testing")
        client.run("alias PkgA/latest@user/testing PkgA/0.1@user/testing")
        client.save({"conanfile.py": GenConanfile().with_require("PkgA/latest@user/testing")})
        client.run("export . PkgB/0.1@user/testing")
        client.run("alias PkgB/latest@user/testing PkgB/0.1@user/testing")
        client.save({"conanfile.py": GenConanfile().with_require("PkgA/latest@user/testing")
                                                   .with_require("PkgB/latest@user/testing")})
        client.run("info .")
        self.assertNotIn("overridden", client.out)

    def test_alias_different_name(self):
        client = TestClient()
        client.run("alias myalias/1.0@user/channel lib/1.0@user/channel", assert_error=True)
        self.assertIn("An alias can only be defined to a package with the same name",
                      client.out)

    def complete_large_test(self):
        # https://github.com/conan-io/conan/issues/2583
        conanfile0 = """from conans import ConanFile
class Pkg(ConanFile):
    pass
"""
        conanfile = """from conans import ConanFile
class Pkg(ConanFile):
    def requirements(self):
        self.requires("%s")
"""
        conanfile2 = """from conans import ConanFile
class Pkg(ConanFile):
    def requirements(self):
        self.requires("%s")
        self.requires("%s")
"""
        conanfile3 = """from conans import ConanFile
class Pkg(ConanFile):
    def requirements(self):
        self.requires("%s")
        self.requires("%s")
        self.requires("%s")
"""
        client = TestClient()

        def export_alias(name, conanfile):
            client.save({"conanfile.py": conanfile})
            client.run("export . %s/0.1@user/testing" % name)
            client.run("alias %s/ALIAS@user/testing %s/0.1@user/testing" % (name, name))

        for name, conanfile in [
            ("CA", conanfile0),
            ("CB", conanfile % "CA/ALIAS@user/testing"),
            ("CC", conanfile % "CA/ALIAS@user/testing"),
            ("CD", conanfile2 % ("CA/ALIAS@user/testing", "CB/ALIAS@user/testing")),
            ("CE", conanfile2 % ("CA/ALIAS@user/testing", "CB/ALIAS@user/testing")),
            ("CF", conanfile2 % ("CA/ALIAS@user/testing", "CB/ALIAS@user/testing")),
            ("CG", conanfile3 %
                ("CA/ALIAS@user/testing", "CD/ALIAS@user/testing", "CB/ALIAS@user/testing")),
            ("CI", conanfile2 % ("CA/ALIAS@user/testing", "CB/ALIAS@user/testing")),
            ("CH", conanfile2 % ("CA/ALIAS@user/testing", "CB/ALIAS@user/testing")),
        ]:
            export_alias(name, conanfile)

        cj = """from conans import ConanFile
class Pkg(ConanFile):
    def build_requirements( self):
        self.requires( "CA/ALIAS@user/testing")
    def requirements( self):
        self.requires( "CB/ALIAS@user/testing")
"""
        export_alias("CJ", cj)

        ck = """from conans import ConanFile
class Pkg(ConanFile):
    def build_requirements( self):
        self.requires( "CA/ALIAS@user/testing")

    def requirements( self):
        self.requires( "CB/ALIAS@user/testing")
        self.requires( "CH/ALIAS@user/testing")
        self.requires( "CI/ALIAS@user/testing")
        self.requires( "CF/ALIAS@user/testing")
        self.requires( "CE/ALIAS@user/testing")
        self.requires( "CD/ALIAS@user/testing")
        self.requires( "CJ/ALIAS@user/testing")
        self.requires( "CG/ALIAS@user/testing")
"""
        export_alias("CK", ck)

        cl = """from conans import ConanFile
class Pkg(ConanFile):
    def build_requirements( self):
        self.requires( "CA/ALIAS@user/testing")

    def requirements( self):
        self.requires( "CI/ALIAS@user/testing")
        self.requires( "CF/ALIAS@user/testing")
        self.requires( "CC/ALIAS@user/testing")
        self.requires( "CJ/ALIAS@user/testing")
        self.requires( "CB/ALIAS@user/testing")
        self.requires( "CH/ALIAS@user/testing")
        self.requires( "CK/ALIAS@user/testing")
"""
        export_alias("CL", cl)

        cm = """from conans import ConanFile
class Pkg(ConanFile):
    def build_requirements( self):
        self.requires( "CA/ALIAS@user/testing")

    def requirements( self):
        self.requires( "CB/ALIAS@user/testing")
        self.requires( "CL/ALIAS@user/testing")
"""
        export_alias("CM", cm)

        consumer = """from conans import ConanFile
class Pkg(ConanFile):
    def build_requirements( self):
        self.requires( "CA/ALIAS@user/testing")

    def requirements( self):
        self.requires( "CD/ALIAS@user/testing")
        self.requires( "CI/ALIAS@user/testing")
        self.requires( "CG/ALIAS@user/testing")
        self.requires( "CM/ALIAS@user/testing")
        self.requires( "CJ/ALIAS@user/testing")
        self.requires( "CK/ALIAS@user/testing")
        self.requires( "CB/ALIAS@user/testing")
        self.requires( "CL/ALIAS@user/testing")
        self.requires( "CH/ALIAS@user/testing")
"""
        client.save({"conanfile.py": consumer})
        client.run("info . --graph=file.dot")
        graphfile = client.load("file.dot")
        self.assertIn('"conanfile.py" -> "CD/0.1@user/testing"', graphfile)
        self.assertIn('"CB/0.1@user/testing" -> "CA/0.1@user/testing"', graphfile)
        self.assertIn('"CD/0.1@user/testing" -> "CA/0.1@user/testing"', graphfile)
        self.assertIn('"CD/0.1@user/testing" -> "CB/0.1@user/testing"', graphfile)
        self.assertIn('"CJ/0.1@user/testing" -> "CB/0.1@user/testing"', graphfile)

    def striped_large_test(self):
        # https://github.com/conan-io/conan/issues/2583
        conanfile0 = """from conans import ConanFile
class Pkg(ConanFile):
    pass
"""
        client = TestClient()

        def export_alias(name, conanfile):
            client.save({"conanfile.py": conanfile})
            client.run("export . %s/0.1@user/testing" % name)
            client.run("alias %s/ALIAS@user/testing %s/0.1@user/testing" % (name, name))

        export_alias("CH", conanfile0)

        ck = """from conans import ConanFile
class Pkg(ConanFile):
    def requirements( self):
        self.requires( "CH/ALIAS@user/testing")
"""
        export_alias("CK", ck)

        cl = """from conans import ConanFile
class Pkg(ConanFile):
    def requirements( self):
        self.requires( "CK/ALIAS@user/testing")
        self.requires( "CH/ALIAS@user/testing")
"""
        export_alias("CL", cl)

        cm = """from conans import ConanFile
class Pkg(ConanFile):
    def requirements( self):
        self.requires( "CL/ALIAS@user/testing")
"""
        export_alias("CM", cm)

        consumer = """from conans import ConanFile
class Pkg(ConanFile):
    def requirements( self):
        self.requires( "CM/ALIAS@user/testing")
        self.requires( "CL/ALIAS@user/testing")
        self.requires( "CK/ALIAS@user/testing")
        self.requires( "CH/ALIAS@user/testing")
"""
        client.save({"conanfile.py": consumer})
        client.run("info . --graph=file.dot")
        graphfile = client.load("file.dot")
        self.assertIn('"CM/0.1@user/testing" -> "CL/0.1@user/testing"', graphfile)
        self.assertIn('"CL/0.1@user/testing" -> "CK/0.1@user/testing"', graphfile)
        self.assertIn('"CL/0.1@user/testing" -> "CH/0.1@user/testing"', graphfile)
        self.assertIn('"CK/0.1@user/testing" -> "CH/0.1@user/testing"', graphfile)

    @parameterized.expand([(True, ), (False, )])
    def test_double_alias_test(self, use_requires):
        # https://github.com/conan-io/conan/issues/2583
        client = TestClient()
        if use_requires:
            conanfile = """from conans import ConanFile
class Pkg(ConanFile):
    requires = "%s"
"""
        else:
            conanfile = """from conans import ConanFile
class Pkg(ConanFile):
    def requirements(self):
        req = "%s"
        if req:
            self.requires(req)
"""

        client.save({"conanfile.py": conanfile % ""}, clean_first=True)
        client.run("export . LibD/0.1@user/testing")
        client.run("alias LibD/latest@user/testing LibD/0.1@user/testing")

        client.save({"conanfile.py": conanfile % "LibD/latest@user/testing"})
        client.run("export . LibC/0.1@user/testing")
        client.run("alias LibC/latest@user/testing LibC/0.1@user/testing")

        client.save({"conanfile.py": conanfile % "LibC/latest@user/testing"})
        client.run("export . LibB/0.1@user/testing")
        client.run("alias LibB/latest@user/testing LibB/0.1@user/testing")

        client.save({"conanfile.py": conanfile % "LibC/latest@user/testing"})
        client.run("export . LibA/0.1@user/testing")
        client.run("alias LibA/latest@user/testing LibA/0.1@user/testing")

        client.save(
                {"conanfile.txt": "[requires]\nLibA/latest@user/testing\nLibB/latest@user/testing"},
                clean_first=True)
        client.run("info conanfile.txt --graph=file.dot")
        graphfile = client.load("file.dot")
        self.assertIn('"LibA/0.1@user/testing" -> "LibC/0.1@user/testing"', graphfile)
        self.assertIn('"LibB/0.1@user/testing" -> "LibC/0.1@user/testing"', graphfile)
        self.assertIn('"LibC/0.1@user/testing" -> "LibD/0.1@user/testing"', graphfile)
        self.assertIn('"conanfile.txt" -> "LibB/0.1@user/testing"', graphfile)
        self.assertIn('"conanfile.txt" -> "LibA/0.1@user/testing"', graphfile)

    @parameterized.expand([(True, ), (False, )])
    def double_alias_options_test(self, use_requires):
        # https://github.com/conan-io/conan/issues/2583
        client = TestClient()
        if use_requires:
            conanfile = """from conans import ConanFile
class Pkg(ConanFile):
    requires = "%s"
    options = {"myoption": [True, False]}
    default_options = "myoption=True"
    def package_info(self):
        self.output.info("MYOPTION: {} {}".format(self.name, self.options.myoption))
"""
        else:
            conanfile = """from conans import ConanFile
class Pkg(ConanFile):
    options = {"myoption": [True, False]}
    default_options = "myoption=True"
    def configure(self):
        if self.name == "LibB":
            self.options["LibD"].myoption = False
    def requirements(self):
        req = "%s"
        if req:
            self.requires(req)
    def package_info(self):
        self.output.info("MYOPTION: {} {}".format(self.name, self.options.myoption))
"""

        client.save({"conanfile.py": conanfile % ""}, clean_first=True)
        client.run("export . LibD/0.1@user/testing")
        client.run("alias LibD/latest@user/testing LibD/0.1@user/testing")

        client.save({"conanfile.py": conanfile % "LibD/latest@user/testing"})
        client.run("export . LibC/0.1@user/testing")
        client.run("alias LibC/latest@user/testing LibC/0.1@user/testing")

        client.save({"conanfile.py": conanfile % "LibC/latest@user/testing"})
        replace_in_file(os.path.join(client.current_folder, "conanfile.py"),
                        '"myoption=True"',
                        '"myoption=True", "LibD:myoption=False"',
                        output=client.out)
        client.run("export . LibB/0.1@user/testing")
        client.run("alias LibB/latest@user/testing LibB/0.1@user/testing")

        client.save({"conanfile.py": conanfile % "LibC/latest@user/testing"})
        client.run("export . LibA/0.1@user/testing")
        client.run("alias LibA/latest@user/testing LibA/0.1@user/testing")

        client.save({"conanfile.txt": "[requires]\nLibA/latest@user/testing\nLibB/latest@user/testing"},
                    clean_first=True)
        client.run("info conanfile.txt --graph=file.dot")
        graphfile = client.load("file.dot")
        self.assertIn('"LibA/0.1@user/testing" -> "LibC/0.1@user/testing"', graphfile)
        self.assertIn('"LibB/0.1@user/testing" -> "LibC/0.1@user/testing"', graphfile)
        self.assertIn('"LibC/0.1@user/testing" -> "LibD/0.1@user/testing"', graphfile)
        self.assertIn('"conanfile.txt" -> "LibB/0.1@user/testing"', graphfile)
        self.assertIn('"conanfile.txt" -> "LibA/0.1@user/testing"', graphfile)
        client.run("install conanfile.txt --build=missing")
        self.assertIn("LibD/0.1@user/testing: MYOPTION: LibD False", client.out)
        self.assertIn("LibB/0.1@user/testing: MYOPTION: LibB True", client.out)
        self.assertIn("LibA/0.1@user/testing: MYOPTION: LibA True", client.out)
        self.assertIn("LibC/0.1@user/testing: MYOPTION: LibC True", client.out)

    @parameterized.expand([(True, ), (False, )])
    def double_alias_ranges_test(self, use_requires):
        # https://github.com/conan-io/conan/issues/2583
        client = TestClient()
        if use_requires:
            conanfile = """from conans import ConanFile
class Pkg(ConanFile):
    requires = "%s"
"""
        else:
            conanfile = """from conans import ConanFile
class Pkg(ConanFile):
    def requirements(self):
        req = "%s"
        if req:
            self.requires(req)
"""

        client.save({"conanfile.py": conanfile % ""}, clean_first=True)
        client.run("export . LibD/sha1@user/testing")
        client.run("alias LibD/0.1@user/testing LibD/sha1@user/testing")

        client.save({"conanfile.py": conanfile % "LibD/[~0.1]@user/testing"})
        client.run("export . LibC/sha1@user/testing")
        client.run("alias LibC/0.1@user/testing LibC/sha1@user/testing")

        client.save({"conanfile.py": conanfile % "LibC/[~0.1]@user/testing"})
        client.run("export . LibB/sha1@user/testing")
        client.run("alias LibB/0.1@user/testing LibB/sha1@user/testing")

        client.save({"conanfile.py": conanfile % "LibC/[~0.1]@user/testing"})
        client.run("export . LibA/sha1@user/testing")
        client.run("alias LibA/0.1@user/testing LibA/sha1@user/testing")

        client.save({"conanfile.txt": "[requires]\nLibA/[~0.1]@user/testing\nLibB/[~0.1]@user/testing"},
                    clean_first=True)
        client.run("info conanfile.txt --graph=file.dot")
        graphfile = client.load("file.dot")
        self.assertIn('"LibA/sha1@user/testing" -> "LibC/sha1@user/testing"', graphfile)
        self.assertIn('"LibB/sha1@user/testing" -> "LibC/sha1@user/testing"', graphfile)
        self.assertIn('"LibC/sha1@user/testing" -> "LibD/sha1@user/testing"', graphfile)
        self.assertIn('"conanfile.txt" -> "LibB/sha1@user/testing"', graphfile)
        self.assertIn('"conanfile.txt" -> "LibA/sha1@user/testing"', graphfile)

    def alias_bug_test(self):
        # https://github.com/conan-io/conan/issues/2252
        client = TestClient()
        client.save({"conanfile.py": GenConanfile()})
        client.run("create . Pkg/0.1@user/testing")
        client.run("alias Pkg/latest@user/testing Pkg/0.1@user/testing")
        client.save({"conanfile.py": GenConanfile().with_require("Pkg/latest@user/testing")})
        client.run("create . Pkg1/0.1@user/testing")
        client.run("create . Pkg2/0.1@user/testing")

        client.save({"conanfile.py": GenConanfile().with_requires("Pkg1/0.1@user/testing",
                                                                  "Pkg2/0.1@user/testing")})
        client.run("create . PkgRoot/0.1@user/testing")
        self.assertNotIn("Pkg/latest@user/testing", client.out)
        self.assertIn("Pkg/0.1@user/testing: Already installed!", client.out)
        self.assertIn("Pkg1/0.1@user/testing: Already installed!", client.out)
        self.assertIn("Pkg2/0.1@user/testing: Already installed!", client.out)

    def transitive_alias_test(self):
        client = TestClient()
        client.save({"conanfile.py": GenConanfile()})
        client.run("create . Pkg/0.1@user/testing")
        client.run("alias Pkg/latest@user/testing Pkg/0.1@user/testing")
        client.run("alias Pkg/superlatest@user/testing Pkg/latest@user/testing")
        client.run("alias Pkg/megalatest@user/testing Pkg/superlatest@user/testing")

        client.save({"conanfile.py":
                     GenConanfile().with_require("Pkg/megalatest@user/testing")})
        client.run("create . Consumer/0.1@user/testing")
        self.assertIn("Pkg/0.1@user/testing: Already installed!", client.out)
        self.assertNotIn("latest@user", client.out)

    def repeated_alias_test(self):
        client = TestClient()
        client.run("alias Hello/0.X@lasote/channel Hello/0.1@lasote/channel")
        client.run("alias Hello/0.X@lasote/channel Hello/0.2@lasote/channel")
        client.run("alias Hello/0.X@lasote/channel Hello/0.3@lasote/channel")

    def test_basic_test(self):
        test_server = TestServer()
        servers = {"default": test_server}
        client = TestClient(servers=servers, users={"default": [("lasote", "mypass")]})
        for i in (1, 2):
            client.save({"conanfile.py": GenConanfile().with_name("Hello").with_version("0.%s" % i)})
            client.run("export . lasote/channel")

        client.run("alias Hello/0.X@lasote/channel Hello/0.1@lasote/channel")
        conanfile_chat = textwrap.dedent("""
            from conans import ConanFile
            class TestConan(ConanFile):
                name = "Chat"
                version = "1.0"
                requires = "Hello/0.X@lasote/channel"
                """)
        client.save({"conanfile.py": conanfile_chat}, clean_first=True)
        client.run("export . lasote/channel")
        client.save({"conanfile.txt": "[requires]\nChat/1.0@lasote/channel"}, clean_first=True)

        client.run("install . --build=missing")

        self.assertIn("Hello/0.1@lasote/channel from local", client.out)
        self.assertNotIn("Hello/0.X@lasote/channel", client.out)
        conaninfo = client.load("conaninfo.txt")
        self.assertIn("Hello/0.1@lasote/channel", conaninfo)
        self.assertNotIn("Hello/0.X@lasote/channel", conaninfo)

        client.run('upload "*" --all --confirm')
        client.run('remove "*" -f')

        client.run("install .")
        self.assertIn("Hello/0.1@lasote/channel from 'default'", client.out)
        self.assertNotIn("Hello/0.X@lasote/channel from", client.out)

        client.run("alias Hello/0.X@lasote/channel Hello/0.2@lasote/channel")
        client.run("install . --build=missing")
        self.assertIn("Hello/0.2", client.out)
        self.assertNotIn("Hello/0.1", client.out)

    def test_not_override_package(self):
        """ Do not override a package with an alias

            If we create an alias with the same name as an existing package, it will
            override the package without any warning.
        """
        t = TestClient()
        conanfile = textwrap.dedent("""
            from conans import ConanFile
            class Pkg(ConanFile):
                description = "{}"
            """)

        # Create two packages
        reference1 = "PkgA/0.1@user/testing"
        t.save({"conanfile.py": conanfile.format(reference1)})
        t.run("export . {}".format(reference1))

        reference2 = "PkgA/0.2@user/testing"
        t.save({"conanfile.py": conanfile.format(reference2)})
        t.run("export . {}".format(reference2))

        # Now create an alias overriding one of them
        alias = reference2
        t.run("alias {alias} {reference}".format(alias=alias, reference=reference1),
              assert_error=True)
        self.assertIn("ERROR: Reference '{}' is already a package".format(alias), t.out)

        # Check that the package is not damaged
        t.run("inspect {} -a description".format(reference2))
        self.assertIn("description: {}".format(reference2), t.out)

        # Remove it, and create the alias again (twice, override an alias is allowed)
        t.run("remove {} -f".format(reference2))
        t.run("alias {alias} {reference}".format(alias=alias, reference=reference1))
        t.run("alias {alias} {reference}".format(alias=alias, reference=reference1))

        t.run("inspect {} -a description".format(reference2))
        self.assertIn("description: None", t.out)  # The alias conanfile doesn't have description
