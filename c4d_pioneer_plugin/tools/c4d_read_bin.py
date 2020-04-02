import os, struct, sys
from colorsys import hsv_to_rgb

def read_bin_file(file_name):
    if os.path.isfile(file_name):

        header_format_desc = [['Номер версии файла', 'B'],
                                ['Стартовый цвет (ргб)', 'B'],
                                ['Частота опроса координат, Гц', 'B'],
                                ['Частота опроса цветов, Гц', 'B'],
                                ['Идентификатор формата координат', 'B'],
                                ['Идентификатор формата цветов', 'B'],
                                ['Количество точек', 'H'],
                                ['Количество цветов', 'H'],
                                ['Время начала миссии, с', 'f'],
                                ['Время окончания миссии, с', 'f'],
                                ['Широта начальной позиции ' + chr(176) + ' с.ш.', 'f'],
                                ['Долгота начальной позиции ' + chr(176) + ' в.д.', 'f'],
                                ['Высота начальной позиции, м', 'f']]
        points_format_desc = [['x, м', 'f'],
                                ['y, м', 'f'],
                                ['z, м', 'f']]
        colors_format_desc = [['hue ', 'B'],
                            ['saturation ', 'B'],
                            ['brightness', 'B']]
        with open(file_name, 'rb') as file:
            header_format = '<' + "".join([i[1] for i in header_format_desc])
            header_format_size = struct.calcsize(header_format)
            check_bytes = file.read(4)
            if check_bytes != b'\xaa\xbb\xcc\xdd':
                print('Неверный формат файла %s' % file_name)
                return
            data = file.read(header_format_size)
            #header = bytearray(size)
            header = struct.unpack(header_format, data)

            if header[0] != 1:
                print('Вывод метаданных данной версии банарных файлов не поддерживается')
                return

            print('Метаданные бинарного файла %s:' % file_name)

            for i in range(len(header)):
                if i == 1:
                    print(header_format_desc[i][0], hsv_to_rgb(int(header[i] * 360 / 255)/360, 1, 1)) # convert from int format to hue and then to rgb
                else:
                    print(header_format_desc[i][0], header[i])
            
            file.read(100 - (header_format_size + 4)) # getting rid of zeros between metadata and points data
            
            start_time = header[8]

            points_num = header[6]
            points_time_step = 1/header[2]
            points_format = '<' + "".join([i[1] for i in points_format_desc])
            points = []
            points_format_size = struct.calcsize(points_format)
            with open(file_name + "_points.txt", 'w') as file_points:
                for i in range(points_num):
                    points_data_read = struct.unpack(points_format, file.read(points_format_size))
                    points.append(points_data_read)
                    #print(start_time + points_time_step*i, points_data_read)
                    file_points.write("{:.2f}s ({:.2f} {:.2f} {:.2f})\n".format(start_time + points_time_step*i, *points_data_read))
            print("{} points written".format(points_num))
            file.read(21700 - (100 + points_format_size*points_num))

            colors_num = header[7]
            colors_time_step = 1/header[3]
            colors_format = '<' + "".join([i[1] for i in colors_format_desc])
            colors = []
            colors_format_size = struct.calcsize(colors_format)
            with open(file_name + "_colors.txt", 'w') as file_colors:
                for i in range(colors_num):
                    colors_data_read = struct.unpack(colors_format, file.read(colors_format_size))

                    colors.append(colors_data_read)
                    #print(start_time + colors_time_step*i, colors_data_read)
                    file_colors.write("{:.2f}s ({:.2f} {:.2f} {:.2f})\n".format(start_time + colors_time_step*i, *[i/255 for i in colors_data_read]))
            print("{} colors written".format(colors_num))
    else:
        print('Файл %s не найден' % file_name)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        read_bin_file(sys.argv[1])
    else:
        print("No bin file to decypher specified, please provide proper filename as an argument")
