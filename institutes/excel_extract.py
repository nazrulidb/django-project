import pandas as pd
import numpy as np

import time, re, regex
from rich.pretty import pprint as pp

from rich.pretty import Pretty
from rich.panel import Panel
from django.contrib.auth import get_user_model

from students.models import StudentRecord
from custom_dashboard.models import BatchUploadResult


def p(v):
    # pp(v)
    # inspect(v)
    pretty = Pretty(v)
    panel = Panel(pretty)
    pp(v, expand_all=True)


def to_json_list(dict):
    json_list = []
    for key in dict.keys():
        row = dict[key]
        if row.__class__.__name__ == "dict" and len(row.keys()) > 1:
            val = to_json_list(row)
            json_list.append({key: val})
        else:
            json_list.append({key: row})
    return json_list


def dict_child_to_list(dict):
    json_list = []
    for key in dict.keys():
        row = dict[key]
        subject = {"Subject": key}
        subject.update(row)
        json_list.append(subject)
    return json_list


class Extractor:
    starting_row = None
    first_col = "Unnamed: 0"
    marker_name = "Sl. No."
    marker_row_count = None
    current_sheet = None
    students_for_update = []
    excel_data = {}
    is_retake = False
    report = {
        'match':0,
        'retake_match':0,
        'total':0,
        'missing':0,
        'students':[],
        'retake_students':[],
        'student_list':[],
        'student_record_saved':[],
        'student_retake_saved':[]
    }

    def __init__(self, file, doc_instance, institute_id):
        self.file = file
        self.sheets = pd.ExcelFile(file).sheet_names
        self.doc_instance = doc_instance
        StudentClass = get_user_model()
        students = StudentClass.objects.filter(institute__id=institute_id, role__name='Student')
        self.name_list = list(students.values_list("username", flat=True))
        
        self.obj_list = students
        self.report['student_list'] = self.name_list

        print(f'all SHEETS {self.sheets}')
        for sheet in self.sheets:
            try:
                print(f"CURRENT SHEET {sheet}")
                self.students_for_update = []
                
                if sheet.lower().startswith("retake"):
                    self.is_retake = True
                else:
                    self.is_retake = False
                self.current_sheet = sheet
                self.get_student_row_starting_point(file=self.file, sheet_name=sheet)

            except Exception as e:
                print(f'ERROR ON SHEET LOOP {e}')
            
            # if self.students_for_update:
            #     r = StudentClass.objects.bulk_update(obj_list, ['metadata'])
        print("EXTRACTOR CALL")
        print("_________________________")

        # with open('new_file.json', 'w+') as f:
        #     # json.dump(self.excel_data, f, indent=)
        #     f.write(json.dumps(self.excel_data, indent = 3))

        #     print("New json file is created from data.json file")

    def get_data(self):
        sheets = [sheet for sheet in self.excel_data.keys()]

        # print(sheets)
        missing = self.report.get('total') - self.report.get('match')
        self.report['missing'] = missing
        self.report['details'] = {
            'level':self.doc_instance.level,
            'term':self.doc_instance.term,
            'year':self.doc_instance.year
        }
        
        return [sheets, self.excel_data, self.report]

    def get_marker_row_count(self):
        df = self.s_df
        count = 0
        # print(df.columns[0])
        # print(len(df[df[self.first_col] == self.marker_name]))
        # print(df.iloc[0])
        self.marker_row_count = len(df[df[self.first_col] == self.marker_name])

        q = df[df[self.first_col] == self.marker_name]
        self.starting_row = [q[:1].iloc[0].name, q[::-1].iloc[0].name]
        # print(f"Marker Cell {self.starting_row}")

    def fill_subject_cell(self):
        df = self.s_df
        df2 = df[:7]
        dff = pd.DataFrame(df2)

        for i in range(self.starting_row[0], self.starting_row[0] + 5):
            # print(i)
            dff.loc[i] = df2.loc[i].ffill()
            self.s_df.loc[i] = df2.loc[i].ffill()

        self.col_headers = dff
        print(f'self.col_headers {self.col_headers}')

    def get_cell_header(self, col_index):
        header = self.col_headers.iloc[0, col_index]
        return header

    def get_cell_attr(self, col_index):
        header = self.get_cell_header(col_index)
        df = self.col_headers.iloc[3]
        # print(df)
        # print("_________")
        # print(df.iloc[col_index])
        cell = str(df.iloc[col_index]).lower()
        has_credit = regex.findall(r"\L<words>", cell, re.IGNORECASE, words=['credit', 'credits'])
        
        if len(has_credit):
            # print("YES CREDIT IN CELL")
            li = cell.split(" ")
            # print(li)
            
            if len(li) == 2:
                df2 = self.col_headers.iloc[1]
                cell = df2.iloc[col_index]
                code = cell.split(":")[1]

                df3 = self.col_headers.iloc[2]
                attr = df3.iloc[col_index]
                
                df4 = self.col_headers.iloc[4]
                ref = df4.iloc[col_index]

                return {"is_subject": True, "credits": li[0], "code": code.strip(), "ref": ref, "attr":attr}

        return {"is_subject": False}

    def get_student_record(self):
        df = self.raw_s_df
        student_df = df[self.marker_row_count :]
        self.student_record_count = len(student_df)
        # print(self.student_record_count)
        # print("starting row")
        # print(self.starting_row[0])
        # print(self.marker_row_count)
        # print(df)

        # pp(student_df)
        data_list = []

        for row_index in range(0, self.student_record_count):
            data = {"Subjects": {}}
            fail_subject_col = self.column_count - 1
            
            for col_index in range(0, self.column_count):
                cell = student_df.iloc[row_index, col_index]
                if type(cell).__name__ == "str":
                    cell = cell.strip()

                header = self.get_cell_header(col_index).strip()
                if type(header).__name__ == "str":
                    header = header.strip()

                if str(cell) == 'nan':
                    cell = ""

                if col_index == 0:
                    data["Sl. No."] = cell
                elif col_index == 1:
                    data["Student's ID"] = cell
                elif col_index == 2:
                    data["Student's Name"] = cell
                elif col_index == 3:
                    data["Year of admission"] = cell
                elif col_index == 4:
                    if not self.is_retake:
                        data['Appeared Subjects'] = cell
                    else:
                        data['Department'] = cell
                elif self.is_retake and col_index == 5:
                    data['Appeared Subjects'] = cell
                elif fail_subject_col == col_index:
                    data['Fail Subjects'] = cell

                else:

                    cell_attr = (self.get_cell_attr(col_index))
                    # print(f'is_subject {cell_attr.get("is_subject")} \n')
                    if cell_attr.get("is_subject"):
                        has_attr = False
                        attr_header = f'{header}({cell_attr.get("attr")})'

                        code = cell_attr.get("code")
                        
                        if header in data['Subjects'] and data['Subjects'][header].get('code') != code:
                            has_attr = True
                            

                        if not header in data["Subjects"]:
                            # print("SUBJECT NOT IN DICT YET")
                            
                            data["Subjects"][header] = {
                                "credits": cell_attr.get("credits"),
                                "attr": cell_attr.get("attr"),
                                "code": code,
                                cell_attr.get("ref"): cell,
                            }
                        
                        elif has_attr:

                            if not attr_header in data["Subjects"]:
                                data["Subjects"][attr_header] = {
                                    "code": code,
                                    "credits": cell_attr.get("credits"),
                                    "attr": cell_attr.get("attr"),
                                    cell_attr.get("ref"): cell,
                                }
                            else:
                                data["Subjects"][attr_header][cell_attr.get("ref")] = cell
                        
                        else:
                            if header == cell:
                                cell = ""
                            
                            data["Subjects"][header][cell_attr.get("ref")] = cell
                    else:
                        # if col_index > 4:
                        if header == cell:
                            cell = ""
                        
                        data[header] = cell
            

            student_id = data.get("Student's ID")
            
            if student_id:
                if not self.is_retake and student_id not in self.report['students']:
                    self.report['students'].append(student_id)
                elif student_id not in self.report['retake_students']:
                    self.report['retake_students'].append(student_id)
                
                s = self.obj_list.filter(username__iexact=student_id).first()
                if s:
                    
                    student_data = data.copy()
                    year_gap = False
                    has_retake = False

                    if self.is_retake:
                        subs_list = None
                        subs = student_data.get('Appeared Subjects')
                        if subs:
                            subs_list = subs.lower().split(',')

                        print(f'Appeared Subjects {subs}')

                        student_subs = student_data.get('Subjects').copy()
                        subjects = student_subs.copy()

                        for k, v in subjects.items():
                            if not v.get('Grade Point') or not v.get('Letter Grade'):
                                student_subs.pop(k)

                        # use to remove subjects base on the subject column code
                        # for k, v in subjects.items():
                        #     res = regex.findall(r"\L<words>", subs, re.IGNORECASE, words=[v.get('code')])
                        #     if not len(res):
                        #         if subs_list and str(k).lower() not in subs_list:
                        #             student_subs.pop(k)
                                
                        student_data['Subjects'] = student_subs

                    else:
                        if student_data.get("Year of admission") != self.doc_instance.exam_held:
                            year_gap = True
                        
                        if data['Fail Subjects']:
                            has_retake = True

                    student_data['details'] = {
                        'level':self.doc_instance.level,
                        'term':self.doc_instance.term,
                        'year':self.doc_instance.year,
                        'exam_held':self.doc_instance.exam_held
                    }
                    
                    try:
                        obj, created = StudentRecord.objects.update_or_create(
                            student=s, record=self.doc_instance, data=student_data, 
                            level=self.doc_instance.level, term=self.doc_instance.term,
                            year=self.doc_instance.year,
                            retake=self.is_retake, year_gap=year_gap, has_retake=has_retake
                        )

                        if not self.is_retake:
                            self.report['match'] = self.report.setdefault('match', 0) + 1
                        else:
                            self.report['retake_match'] = self.report.setdefault('retake_match', 0) + 1

                        if created:
                            if not self.is_retake and student_id not in self.report['student_record_saved']:
                                self.report['student_record_saved'].append(student_id)
                            elif student_id not in self.report['student_retake_saved']:
                                self.report['student_retake_saved'].append(student_id)
                        
                    except Exception as e:
                        print("ERROR ON CREATING STUDENT RECORD")
                        print(e)
            

                    
                data["Subjects"] = data.pop("Subjects")
                data_copy = data.copy()
                try:
                    
                    dl = list(data_copy.items())

                    if data_copy.get("CGPA"):
                        cgpa = data_copy.pop("CGPA")
                        dl.insert(3, ("CGPA", cgpa))

                    if data_copy.get("Result"):
                        res = data_copy.pop("Result")
                        dl.insert(4, ("Result", res))
                    
                    if data_copy.get("Term GPA"):
                        gpa = data_copy.pop("Term GPA")
                        dl.insert(5, ("Term GPA", gpa))
            

                    data = dict(dl)

                except Exception as e:
                    print("ERROR ON GRADE ASSERTION")
                    print(e)

                self.report['total'] = self.report.setdefault('total', 0) + 1
                # print(f'TOTAL STUDENT COUNT {self.report["total"]}')
                data_list.append(data)

        
        self.excel_data[self.current_sheet] = data_list

    def get_student_row_starting_point(self, file, sheet_name):
        self.raw_df = pd.read_excel(file, sheet_name=sheet_name)

        self.raw_df.index = pd.Series(self.raw_df.index).fillna("None")
        self.df = pd.DataFrame(self.raw_df)

        self.df = self.df
        self.rows = self.df
        self.rows_count = len(self.df)
        self.column_count = len(self.df.columns)

        try:
            marker = np.where(self.df == self.marker_name)[0][0]
        except Exception as e:
            print('ERROR ON ROW STARTING POINT')
            print(e)
            marker = None
        print("________________________________________________")
        # print(self.current_sheet)
        # print(marker)

        if marker:
            student_df = self.df.truncate(before=marker, after=self.rows_count)
            student_df = pd.DataFrame(student_df)
            self.raw_s_df = student_df
            
            student_df2 = student_df.ffill()
            student_df2[self.first_col] = student_df[self.first_col].fillna(
                method="ffill"
            )

            # print(list(student_df.columns.values))

            # print(student_df2)
            # print(student_df2.iloc[0, 0])
            self.s_df = student_df2
            
            try:
                self.get_marker_row_count()
            except Exception as e:
                print(f'ERROR ON GET MARKER {e}')

            try:
                self.fill_subject_cell()
            except Exception as e:
                print(f'ERROR ON FILL SUBJECT {e}')

            try:
                self.get_student_record()
            except Exception as e:
                print(f'ERROR ON GET STUDENT RECORD {e}')


            print(f'sheet {self.current_sheet} done')