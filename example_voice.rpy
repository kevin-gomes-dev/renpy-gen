# Basic way to dynamically get each sound file in order such that "voice get_sound()" will keep getting next one
define voice_file_index = 0
init python:
    audio_file_list = [i for i in renpy.list_files() if 'audio/' in i]
    audio_file_list.sort()
    def get_sound():
        global voice_file_index
        if voice_file_index >= len(audio_file_list):
            voice_file_index = len(audio_file_list) - 1
        ret = audio_file_list[voice_file_index]
        voice_file_index += 1
        return ret