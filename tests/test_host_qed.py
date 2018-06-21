import requests
import unittest
import numpy.testing as npt
from bs4 import BeautifulSoup
import mechanicalsoup # for populating and submitting input data forms
import unicodedata
from tabulate import tabulate
from . import linkcheck_helper
import numpy as np
import json


pub_server = "http://qed.epa.gov/pram/"
internal_server_1 = "http://qedinternal.epa.gov/pram/"
internal_server_5 = "http://134.67.114.5/pram/"


servers = [pub_server, internal_server_1, internal_server_5]

models = ["agdrift/", "beerex/", "iec/", "sip/", "stir/", 'terrplant/', 'therps/', 'trex/',
          'kabam/', 'rice/', 'agdisp/', 'earthworm/', 'insect/', 'pat/', 'perfum/', 'pfam/',
          'pwc/', 'sam/', 'ted/', 'varroapop/']

models_nonbeta = ["agdrift/", "beerex/", "iec/", "sip/", "stir/", 'terrplant/', 'therps/', 'trex/',
          'kabam/', 'rice/']
#The following list represents the model page titles to be checked (order of models
#needs to be the same as "models" list above)

models_IO = ["AgDrift", "Bee-REX", "IEC", "SIP", "STIR", "TerrPlant", "T-HERPS", 'T-REX 1.5.2',
                 "KABAM", "RICE", "Agdisp", "Earthworm", "Insect", "Pat", "Perfum", "Pfam",
                 "PWC", "SAM", "TED", "VarroaPop"]
                            
models_IO_nonbeta = ["AgDrift", "Bee-REX", "IEC", "SIP", "STIR", "TerrPlant", "T-HERPS", 'T-REX 1.5.2',
                 "KABAM", "RICE"]


pages = ["","input", "algorithms", "references"] #for now leaving out "qaqc" page

#redirect servers are those where user login fthe input page is required
redirect_servers = [pub_server]
redirect_pages = ["input"]

#following are lists of url's to be processed with tests below
model_pages = [s + m + p for s in servers for m in models for p in pages]
redirect_model_pages = [s + m + p for s in redirect_servers for m in models
                        for p in redirect_pages]
redirect_models = models_IO * len(redirect_servers)

#all models
pub_model_pages = [pub_server + m + p for m in models for p in pages]
s1_model_pages = [internal_server_1 + m + p for m in models for p in pages]
s5_model_pages = [internal_server_5 + m + p for m in models for p in pages]

#non-beta only
pub_model_pages_nonbeta = [pub_server + m + p for m in models_nonbeta for p in pages]
s1_model_pages_nonbeta = [internal_server_1 + m + p for m in models_nonbeta for p in pages]
s5_model_pages_nonbeta = [internal_server_5 + m + p for m in models_nonbeta for p in pages]

#hooks for the qed_smoketests Slack app
pub_server_hook = 'https://hooks.slack.com/services/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'
s1_hook = 'https://hooks.slack.com/services/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'
s5_hook = 'https://hooks.slack.com/services/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'

class TestQEDHost(unittest.TestCase):
    """
    this testing routine accepts a list of servers where a group of models and pages (i.e.,tabs)
    are presented as web pages.  it is assumed that the complete set of models and related pages
    are present on each server. this routine performs a series of unit tests that ensure
    that the web pages are up and operational.
    """

    def setup(self):
        pass

    def teardown(self):
        pass
    
    def send_slack_message(self,message, hook_url):
       body = {"text": message}
       url = hook_url
       response = requests.post(url, data=json.dumps(body), headers = {'Content-type': 'application/json'})
       return


    def helper_response(self,page_list, code, hook_url=None):
        test_name = "Model page access "
        print(str(page_list))
        assert_error = False
        response = [requests.get(m, verify=False).status_code for m in page_list]
        print(response)
        try:
            assert all(resp == code for resp in response)
                #assert(npt.assert_array_equal(response, 200, '200 error', True)
        except AssertionError as e:
            fail_indices = np.where(np.array([resp != code for resp in response]))
            print(fail_indices)
            fails = [page_list[i] for i in np.nditer(fail_indices)]
            codes = [response[i] for i in np.nditer(fail_indices)]
            message = tuple(["Http response failed for: " + str(x) + ". Expecting *" + str(code) + "* but found *" +
                             str(y) + "*." for x, y  in zip(fails,codes)])
            if(hook_url is not None):
                self.send_slack_message("\n".join(message), hook_url)
            e.args += message
            raise
        return


    #public server should return redirects to the login page
    def test_pub_server_303(self):
        self.helper_response(pub_model_pages,200, pub_server_hook)
        return

    def test_internal_s1_200(self):
        self.helper_response(s1_model_pages,200,s1_hook )
        return

    def test_interval_s5_200(self):
        self.helper_response(s5_model_pages,200, s5_hook)



    @staticmethod
    def te_st_qed_404():
        test_name = "Model page 404 "
        try:
            assert_error = False
            response = [requests.get(m) for m in model_pages]
            check_of404 = ["Ok"] * len(response)
            assume_no404 = [False] * len(response)  #assume no 404 in page html
            page_content = [BeautifulSoup(r.content, "html.parser") for r in response]
            find_N404s = [len(s.findAll('img',src='/static/images/404error.png')) for s in page_content]
            did_we_find404 = [s>0 for s in find_N404s]
            for item in did_we_find404:
                if item == True:
                    check_of404[item] = "Found 404"
            try:
                npt.assert_array_equal(did_we_find404, assume_no404, '404 error', True)
            except AssertionError:
                assert_error = True
            except Exception as e:
                # handle any other exception
                print("Error: {}".format(str(e)))
        except Exception as e:
            # handle any other exception
            print("Error: {}".format(str(e)))
        finally:
            linkcheck_helper.write_report(test_name, assert_error, model_pages, check_of404)
        return

    @staticmethod
    def te_st_qed_redirect():  #redirects occur on 'input' pages due to login requirement
        test_name = "Model Input Page Redirect "
        try:
            response = [requests.get(m) for m in redirect_model_pages]
            assert_error = False
            check_of302 = ["302 Failed"] * len(response)
            did_we_find302 = [False] * len(response)
            assume302 = [True] * len(response)  # we're expecting 302 as response history
            for idx, r in enumerate(response):
                for resp in r.history:
                    if resp.status_code == 302:
                        did_we_find302[idx] = True
                        check_of302[idx] = "Ok"
            try:
                npt.assert_array_equal(did_we_find302, assume302, '302 error', True)
            except AssertionError:
                assert_error = True
            except Exception as e:
                # handle any other exception
                print("Error: {}".format(str(e)))
        except Exception as e:
            # handle any other exception
            print("Error: {}".format(str(e)))
        finally:
            linkcheck_helper.write_report(test_name, assert_error, redirect_model_pages, check_of302)
        return

    @staticmethod
    def te_st_qed_authenticate_input():
        test_name = "Model Input Page Login Authentication "
        try: #need to login and then verify we land on input page
            current_page = [""] * len(redirect_model_pages)
            expected_page = [""] * len(redirect_model_pages)
            assert_error = False
            for idx, m in enumerate(redirect_model_pages) :
                br = mechanicalsoup.StatefulBrowser()
                br.open(m)
                #step 1: login and authenticate
                br.select_form('form[name="auth"]')
                br["username"] = "qeduser"
                br["password"] = "EcoDom18!PubServ3"
                br.submit_selected()
                # Verify we have successfully logged in and are now on input page
                current_page[idx] = br.get_url()
                expected_page[idx] = m
            try:
                npt.assert_array_equal(expected_page, current_page, 'Login Failed', True)
            except AssertionError:
                assert_error = True
            except Exception as e:
                # handle any other exception
                print("Error: {}".format(str(e)))
        except Exception as e:
            # handle any other exception
            print("Error: {}".format(str(e)))
        finally:
            linkcheck_helper.write_report(test_name, assert_error, expected_page, current_page)
        return

    @staticmethod
    def te_st_qed_input_form():
        test_name = "Model Input Page Generation "
        try: #need to repeat login and then verify title of input page
            assert_error = False
            current_title = [""] * len(redirect_model_pages)
            expected_title = [""] * len(redirect_model_pages)
            for idx, m in enumerate(redirect_model_pages):
                # Create browser object
                br = mechanicalsoup.StatefulBrowser()
                br.open(m)
                #step 1: login and authenticate
                br.select_form('form[name="auth"]')
                br["username"] = "qeduser"
                br["password"] = "EcoDom18!PubServ3"
                response2 = br.submit_selected()
                response2.get_data()
                #locate model input page title and verify it is as expected
                soup = BeautifulSoup(response2, "html.parser")
                tag = [a.find(text=True) for a in soup.findAll('h2', {'class': 'model_header'})]
                current_title[idx] = m.replace("input", "") + ": " + str(tag[0])
                expected_title[idx] = m.replace("input", "") + ": " + redirect_models[idx] + " Inputs"
                #create array comparison ((assume h2/model header -tag- of interest is first in list)
            try:
                npt.assert_array_equal(current_title, expected_title,'Wrong Input Page Title', True)
            except AssertionError:
                assert_error = True
            except Exception as e:
                # handle any other exception
                print("Error: {}".format(str(e)))
        except Exception as e:
            # handle any other exception
            print("Error: {}".format(str(e)))
        finally:
            linkcheck_helper.write_report(test_name, assert_error, expected_title, current_title)
        return

    @staticmethod
    def te_st_qed_output_form():
        test_name = "Model output generation "
        try:        #need to repeat login, submit default inputs, and verify we land on output page
            assert_error = False
            current_title = [""] * len(redirect_model_pages)
            expected_title = [""] * len(redirect_model_pages)
            for idx, m in enumerate(redirect_model_pages) :
                br = mechanicalsoup.StatefulBrowser()
                response = br.open(m)
                #step 1: login and authenticate
                br.select_form('form[name="auth"]')
                br["username"] = "qeduser"
                br["password"] = "EcoDom18!PubServ3"
                response2 = br.submit_selected()
                response2.get_data()
                # Step 2: Select and submit input form (it will have default data in it  -  we just want to run with that for now)
                try:
                    br.form = (br.select_form(1)) # select the second form on the page (skipping search bar form)
                    response3 = br.submit()  # use mechanize to post input data
                    response3.get_data()
                    #Verify we have successfully posted input data and that we have arrived at the output page
                    soup = BeautifulSoup(response3, "html.parser")
                    tag = [a.find(text=True) for a in soup.findAll('h2', {'class': 'model_header'})]
                    current_title[idx] = m.replace("input", "") + ": " + str(tag[0])
                    expected_title[idx] = m.replace("input", "") + ": " + redirect_models[idx] + " Output"
                except Exception:
                    current_title[idx] = m.replace("input", "") + ": " + "No " + redirect_models[idx] + " Output"
                    expected_title[idx] = m.replace("input", "") + ": " + redirect_models[idx] + " Output"
            try:
                #create array comparison (assume h2/model header -tag- of interest is first in list)
                npt.assert_array_equal(current_title, expected_title,'Submittal of Input Failed for one or more models', True)
            except AssertionError:
                assert_error = True
            except Exception as e:
                # handle any other exception
                print("Error: {}".format(str(e)))
        except Exception as e:
            # handle any other exception
            print("Error: {}".format(str(e)))
        finally:
            linkcheck_helper.write_report(test_name, assert_error, expected_title, current_title)
        return


# unittest will
# 1) call the setup method,
# 2) then call every method starting with "test",
# 3) then the teardown method
if __name__ == '__main__':
    unittest.main()
