import requests
import unittest
import numpy.testing as npt
from bs4 import BeautifulSoup
import mechanicalsoup # for populating and submitting input data forms
import unicodedata
from tabulate import tabulate
from . import linkcheck_helper
from . import smoketest_secrets
import numpy as np
import json


pub_server = "https://qed.epa.gov/"
internal_server_1 = "https://qedinternal.epa.gov/"
internal_server_5 = "http://134.67.114.5/"


servers = [pub_server, internal_server_1, internal_server_5]

models = ["agdrift/", "beerex/", "iec/", "sip/", "stir/", 'terrplant/', 'therps/', 'trex/',
          'kabam/', 'rice/', 'agdisp/', 'earthworm/', 'insect/', 'pat/', 'perfum/', 'pfam/',
          'pwc/', 'sam/', 'ted/', 'varroapop/']

models_nonbeta = ["agdrift/", "beerex/", "iec/", "sip/", "stir/", 'terrplant/', 'therps/', 'trex/',
          'kabam/', 'rice/']


models_IO = ["AgDrift", "Bee-REX", "IEC", "SIP", "STIR", "TerrPlant", "T-HERPS", 'T-REX 1.5.2',
                 "KABAM", "RICE", "Agdisp", "Earthworm", "Insect", "Pat", "Perfum", "Pfam",
                 "PWC", "SAM", "TED", "VarroaPop"]
                            

non_pram_modules = ["cts/", "hms/", 'pisces/', 'pisces/watershed/', 'pisces/stream/', 'pisces/species/', 'pisces/algorithms/',
                    'pisces/references/','hwbi/', 'wqt/', 'hem/', 'cyan/']


pages = ["","input", "algorithms", "references"] #for now leaving out "qaqc" page


#all pram models
pub_model_pages_pram = [pub_server + 'pram/' + m + p for m in models for p in pages]
s1_model_pages_pram = [internal_server_1  + 'pram/' + m + p for m in models for p in pages]
s5_model_pages_pram = [internal_server_5  + 'pram/' + m + p for m in models for p in pages]


#non-beta pram only
pub_model_pages_pram_nonbeta = [pub_server  + 'pram/'+ m + p for m in models_nonbeta for p in pages]
s1_model_pages_pram_nonbeta = [internal_server_1  + 'pram/'+ m + p for m in models_nonbeta for p in pages]
s5_model_pages_pram_nonbeta = [internal_server_5 + 'pram/' + m + p for m in models_nonbeta for p in pages]


#non-pram modules
pub_model_pages_other = [pub_server + m for m in non_pram_modules]
s1_model_pages_other = [internal_server_1  + m for m in non_pram_modules]
s5_model_pages_other= [internal_server_5  + m for m in non_pram_modules]

#combine pram pages and the base-level non-pram modules
pub_model_pages = pub_model_pages_pram + pub_model_pages_other
s1_model_pages = s1_model_pages_pram + s1_model_pages_other
s5_model_pages = s5_model_pages_pram + s5_model_pages_other




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

    def send_slack_message(self,message, hook_url, server = None):
        pages_down = message.count('\n') + 1
        if pages_down > 2:
            if server is not None:
                body = {"text": "There are *" + str(pages_down) + "* pages down on " + server,
                        "attachments": [
                            {
                                "text": message
                            }
                        ]
                        }
            else:
                body = {"text": "There are " + str(pages_down) + " pages down.",
                        "attachments": [
                            {
                                "text": message
                            }
                        ]
                        }
        else:
            body = {"text": message}
        url = hook_url
        response = requests.post(url, data=json.dumps(body), headers={'Content-type': 'application/json'})
        return


#checks if the amount of pages down equals ALL pages, in which case return a different message
    def are_all_down(self, message, page_list, server = None):
        pages_down = message.count('\n')+1
        if pages_down > len(page_list)*.95:
            if(server is not None):
                return server + " is down!"
            else:
                return "All pages are down!"
        else:
            return message

    def check_response(self, page_list, code, hook_url=None, server=None, login=False, verify=True):
        test_name = "Model page access "
        if login:
            response = [None for x in range(0, len(page_list))]
            for x, val in enumerate(page_list):
                print(val)
                br = mechanicalsoup.StatefulBrowser(raise_on_404=False)
                initial_response = br.open(val)
                if initial_response.status_code < 400:
                    # login and authenticate
                    br.select_form('form[name="auth"]')
                    br["username"] = smoketest_secrets.qed_user
                    br["password"] = smoketest_secrets.qed_pass
                    response2 = br.submit_selected()
                    response[x] = response2.status_code
                else:
                    response[x] = initial_response.status_code
        else:
            response = [requests.get(m, verify=verify).status_code for m in page_list]
        try:
            assert all(resp == code for resp in response)
                # assert(npt.assert_array_equal(response, 200, '200 error', True)
        except AssertionError as e:
            fail_indices = np.where(np.array([resp != code for resp in response]))
            print(fail_indices)
            fails = [page_list[i] for i in np.nditer(fail_indices)]
            codes = [response[i] for i in np.nditer(fail_indices)]
            message = tuple(["Http response failed for: " + str(x) + ". Expecting *" + str(code) + "* but found *" +
                             str(y) + "*." for x, y in zip(fails, codes)])
            slack_message = self.are_all_down("\n".join(message), page_list, server)
            if hook_url is not None:
                self.send_slack_message(slack_message, hook_url, server)
            e.args += message
            raise
        return




    #THE TESTS
    def test_pub_server_200(self):
        self.check_response(pub_model_pages, 200, smoketest_secrets.pub_server_hook, pub_server, login=True)
        return

    def test_internal_s1_200(self):
        self.check_response(s1_model_pages, 200, smoketest_secrets.s1_hook, internal_server_1)
        return

    def test_interval_s5_200(self):
        self.check_response(s5_model_pages, 200, smoketest_secrets.s5_hook, internal_server_5, verify=False)




    def check_output(self, page_list, code, hook_url=None, server=None, login = False, verify=True):
        test_name = "Check if model runs and displays output page"
        if login:
            response = [None for x in range(0,len(page_list))]
            for x, val in enumerate(page_list):
                print(val)
                br = mechanicalsoup.StatefulBrowser(raise_on_404=False)
                initial_response = br.open(val)
                if initial_response.status_code < 400:
                    #login and authenticate
                    br.select_form('form[name="auth"]')
                    br["username"] = smoketest_secrets.qed_user
                    br["password"] = smoketest_secrets.qed_pass
                    response2 = br.submit_selected()
                    response[x] = response2.status_code
                    br.form = (br.select_form(1))  # select the second form on the page (skipping search bar form)
                    response3 = br.submit_selected()  # use mechanize to post input data
                    response3.get_data()
                    # Verify we have successfully posted input data and that we have arrived at the output page
                    soup = BeautifulSoup(response3, "html.parser")
                    tag = [a.find(text=True) for a in soup.findAll('h2', {'class': 'model_header'})]
                    current_title = val.replace("input", "") + ": " + str(tag[0])
                    expected_title = val.replace("input", "") + ": " + redirect_models[idx] + " Output"
                else:
                    response[x] = "fail"
        else:
            response = [requests.get(m, verify=verify).status_code for m in page_list]
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
            slack_message = self.are_all_down("\n".join(message), page_list, server)
            if hook_url is not None:
                self.send_slack_message(slack_message, hook_url, server)
            e.args += message
            raise
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


    def input_form_login(self, page_list, code, hook_url=None, server=None):
        assert_error = False
        current_status = [None for x in len(page_list)]
        expected_status = 200
        for idx, m in enumerate(page_list):
            # Create browser object
            br = mechanicalsoup.StatefulBrowser()
            br.open(m)
            #step 1: login and authenticate
            br.select_form('form[name="auth"]')
            br["username"] = "qeduser"
            br["password"] = "EcoDom18!PubServ3"
            response2 = br.submit_selected()
            current_status[idx] = response2.status_code
        try:
            assert all(status == expected_status for status in expected_status)
        except AssertionError as e:
            fail_indices = np.where(np.array([status != code for status in expected_status]))
            print(fail_indices)
            fails = [page_list[i] for i in np.nditer(fail_indices)]
            codes = [expected_status[i] for i in np.nditer(fail_indices)]
            message = tuple(["QED public - input page inaccessible for: " + str(x) + ". Expecting *" + str(code) + "* but found *" +
                             str(y) + "*." for x, y in zip(fails, codes)])
            slack_message = self.are_all_down("\n".join(message), page_list, server)
            if (hook_url is not None):
                self.send_slack_message(slack_message, hook_url, server)
            e.args += message
            raise


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
