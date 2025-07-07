import os
import PySimpleGUI as sg
import openpyxl
from datetime import datetime

class FileComparatorApp:
    def __init__(self):
        sg.theme('SystemDefault')
        self.layout = self.create_layout()
        self.window = sg.Window("文件比较器", self.layout, size=(700, 500))

    def create_layout(self):
        layout = [
            [sg.Text("文件夹一 (源):"), sg.Input(key='-FOLDER1-'), sg.FolderBrowse('选择...', target='-FOLDER1-')],
            [sg.Text("文件类型 (如 .DAT):", size=(18,1)), sg.InputText('.DAT', key='-TYPE1-', size=(15,1))],
            [sg.Text("文件夹二 (目标):"), sg.Input(key='-FOLDER2-'), sg.FolderBrowse('选择...', target='-FOLDER2-')],
            [sg.Text("文件类型 (如 .DXF):", size=(18,1)), sg.InputText('.DXF', key='-TYPE2-', size=(15,1))],
            [sg.Button("开始比较并生成Excel", size=(20, 2))],
            [sg.Text("", key='-STATUS-', size=(50, 1), text_color='blue')]
        ]
        return layout

    def run(self):
        while True:
            event, values = self.window.read()
            if event == sg.WIN_CLOSED:
                break
            if event == "开始比较并生成Excel":
                self.compare_files(values)
        self.window.close()

    def compare_files(self, values):
        folder1 = values['-FOLDER1-']
        file_type1 = values['-TYPE1-']
        folder2 = values['-FOLDER2-']
        file_type2 = values['-TYPE2-']

        if not all([folder1, file_type1, folder2, file_type2]):
            sg.popup_error("错误", "所有字段都必须填写！")
            return

        if not os.path.isdir(folder1) or not os.path.isdir(folder2):
            sg.popup_error("错误", "选择的路径不是有效的文件夹！")
            return

        self.window['-STATUS-'].update("正在比较文件...")
        self.window.refresh()

        try:
            files_to_update = []
            for filename1 in os.listdir(folder1):
                if filename1.upper().endswith(file_type1.upper()):
                    base_name = os.path.splitext(filename1)[0]
                    file2_name = base_name + file_type2
                    path1 = os.path.join(folder1, filename1)
                    path2 = os.path.join(folder2, file2_name)

                    if os.path.exists(path2):
                        mtime1 = os.path.getmtime(path1)
                        mtime2 = os.path.getmtime(path2)

                        # 添加1秒的时间容差，避免浮点数精度问题
                        if mtime2 > mtime1 + 0.1:
                            files_to_update.append({
                                'file_name': filename1,
                                'path1': path1,
                                'mtime1': datetime.fromtimestamp(mtime1).strftime('%Y-%m-%d %H:%M:%S'),
                                'path2': path2,
                                'mtime2': datetime.fromtimestamp(mtime2).strftime('%Y-%m-%d %H:%M:%S')
                            })
            
            if files_to_update:
                self.export_to_excel(files_to_update)
            else:
                sg.popup("完成", "没有找到需要更新的文件。")

        except Exception as e:
            sg.popup_error("错误", f"发生错误: {e}")
        finally:
            self.window['-STATUS-'].update("")

    def export_to_excel(self, file_list):
        save_path = sg.popup_get_file(
            '保存Excel文件',
            save_as=True,
            default_extension=".xlsx",
            file_types=(("Excel 文件", "*.xlsx"),),
            initial_folder=os.getcwd(),
            default_path="待更新文件列表.xlsx"
        )

        if not save_path:
            self.window['-STATUS-'].update("操作已取消")
            return

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "待更新文件"

        headers = ["文件名 (源)", "源文件路径", "源文件修改日期", "目标文件路径", "目标文件修改日期"]
        ws.append(headers)

        for item in file_list:
            ws.append([item['file_name'], item['path1'], item['mtime1'], item['path2'], item['mtime2']])

        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except:
                    pass
            adjusted_width = (max_length + 2)
            ws.column_dimensions[column].width = adjusted_width

        try:
            wb.save(save_path)
            sg.popup("成功", f"成功生成Excel文件: \n{save_path}")
        except Exception as e:
            sg.popup_error("错误", f"保存Excel文件失败: {e}")
        finally:
            self.window['-STATUS-'].update("")

if __name__ == "__main__":
    app = FileComparatorApp()
    app.run()