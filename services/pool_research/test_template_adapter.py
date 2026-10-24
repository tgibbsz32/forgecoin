import unittest
from services.pool_research.template_adapter import validate_template, TemplateError

def fixture():
    return {"result":{"status":"OK","untrusted":False,"height":17,"difficulty":500000,"expected_reward":2384185222,
      "seed_hash":"ab"*32,"blocktemplate_blob":"00"*160,
      "blockhashing_blob":"10"*90,"reserved_offset":95}}

class TemplateTests(unittest.TestCase):
    def test_reject_unsuccessful_or_untrusted(self):
        for field, values in (("status", (None, "BUSY", "Failed", "")),
                              ("untrusted", (None, True, 0, "false"))):
            for value in values:
                with self.subTest(field=field, value=value), self.assertRaises(TemplateError):
                    obj = fixture()
                    obj["result"][field] = value
                    validate_template(obj)
            with self.subTest(missing=field), self.assertRaises(TemplateError):
                obj = fixture()
                del obj["result"][field]
                validate_template(obj)

    def test_valid(self):
        t=validate_template(fixture())
        self.assertEqual((t.height,t.reserve_size,t.reserved_offset),(17,8,95))
        self.assertEqual(len(t.seed_hash),32)
    def test_reject_invalid(self):
        edits=[
          ("difficulty",0),("difficulty","500000"),("seed_hash","zz"*32),
          ("blocktemplate_blob","00"),("reserved_offset",158),
          ("height",-1),("expected_reward",1.2),("blockhashing_blob","00")
        ]
        for field,value in edits:
            with self.subTest(field=field),self.assertRaises(TemplateError):
                obj=fixture();obj["result"][field]=value
                validate_template(obj)
    def test_rpc_error(self):
        with self.assertRaises(TemplateError):
            validate_template({"error":{"code":-1,"message":"unavailable"}})
if __name__=="__main__":unittest.main()
