import logging
import pathlib
import xml.etree.ElementTree as ET
import hashlib
import pprint

import attr

@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class Entry:

    file_name:pathlib.Path() = attr.ib()
    file_size:int = attr.ib()
    file_sha1:str = attr.ib()
    file_md5:str = attr.ib()

@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class ErrorResult:

    entry:Entry = attr.ib()
    reason:str = attr.ib()

class Application:
    '''the main application
    '''

    def __init__(self, logger, args):
        ''' constructor
        @param logger the Logger instance
        @param args - the namespace object we get from argparse.parse_args()
        '''

        self.logger = logger
        self.args = args

        self.error_list = list()
        self.match_list = list()
        self.nomatch_list = list()

        self.entry_list = list()
        self.files_xml_file = self.args.files_xml_file
        self.local_files_folder = self.args.local_files_folder
        self.output_folder = self.args.output_folder

        with open(self.files_xml_file, "r", encoding="utf-8") as f:
            self.tree = ET.parse(f)


        for iter_file_tag in self.tree.getroot().iter("file"):

            e_name = pathlib.Path(iter_file_tag.attrib["name"])
            e_size = None
            e_sha1 = None
            e_md5 = None
            for iter_sub_tag in iter_file_tag:

                tag_name = iter_sub_tag.tag

                if tag_name == "size":
                    e_size = int(iter_sub_tag.text)
                elif tag_name == "sha1":
                    e_sha1 = iter_sub_tag.text
                elif tag_name == "md5":
                    e_md5 = iter_sub_tag.text


            new_entry = Entry(
                file_name=e_name,
                file_size=e_size,
                file_sha1=e_sha1,
                file_md5=e_md5)

            self.logger.debug("new entry: `%s`", new_entry)

            self.entry_list.append(new_entry)




    def run(self):




        for     iter_entry in self.entry_list:

            self.logger.info("on entry `%s`", iter_entry)

            local_file_path = self.local_files_folder / iter_entry.file_name

            # check to make sure the file exists and is a file
            if not local_file_path.exists() or not local_file_path.is_file():
                self.logger.error("the file `%s` doesn't exist or is not a file!", local_file_path)

                self.error_list.append(ErrorResult(
                    entry=iter_entry,
                    reason=f"the local file `{local_file_path}` doesn't exist or is not a file"))

            # validate the file attributes now

            stat_result = local_file_path.stat()

            size_result = iter_entry.file_size == stat_result.st_size

            sha_hasher = hashlib.sha1()
            md5_hasher = hashlib.md5()

            with open(local_file_path, "rb") as f:

                while True:

                    data = f.read(4096)

                    if not data:
                        break
                    else:

                        sha_hasher.update(data)
                        md5_hahser.update(data)

            md5_hex = md5_hahser.hexdigest()
            sha1_hex = sha_hasher.hexdigest()

            self.logger.debug("md5 hex: `%s`, sha1 hex: `%s`", md5_hex, sha1_hex)

            md5_result = md5_hex == iter_entry.file_md5
            sha1_result = sha1_hex == iter_entry.file_sha1


            final_result = size_result and md5_result and sha1_result

            self.logger.debug("size result: `%s`, md5 result: `%s`, sha1 result: `%s`, final result: `%s`",
                size_result, md5_result, sha1_result, final_result)

            if final_result:
                self.match_list.append(iter_entry)

            else:
                self.nomatch_list.append(iter_entry)


            iso_str = str(arrow.utcnow().timestamp)

            out_folder = self.output_folder / f"{iso_str}_compare_files_to_ia_upload_results"

            error_path = out_folder / "errors.txt"
            match_path = out_folder / "matches.txt"
            nomatch_path = out_folder / "nomatches.txt"

            with open(error_path, "w", encoding="utf-8") as f:

                f.write(pprint.pformat(self.error_list))


            with open(match_path, "w", encoding="utf-8") as f:

                f.write(pprint.pformat(self.match_list))

            with open(nomatch_path, "w", encoding="utf-8") as f:

                f.write(pprint.pformat(self.nomatch_list))
