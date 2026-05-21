from dialogue_manager import DialogueManager
from dialogue import Dialogue
import os

# Assumes name to use underscores
# Default emotions are 3 happy, 3 angry, 3 sad, cry, embarrass, normal, 2 fear, curious, laugh, 4 lust, surprise, and close
# Use invisible flag to have all img statements be blank. For exapmple, if you don't have a character image yet
def get_char_img_dict(char_img_name,
                      char_letter_code,
                      emotions=['happy','happy2','happy3','angry','angry2','angry3','sad','sad2','sad3','cry','embarrassed','normal',
                       'fear','fear2','curious','laugh','lust','lust2','lust3','lust4','surprise','close'],
                      short_emo = ['H','HH','HHH','A','AA','AAA','S','SS','SSS','U','E','','F','FF','C','Y','L','LL','LLL','LLLL','P','Z'],
                      invisible_flag = False):
    img_dict = {}
    for i in range(len(short_emo)):
        if not invisible_flag:
            img_dict[char_letter_code + short_emo[i]] = f'show {char_img_name} {emotions[i]} with dissolve'
        else:
            img_dict[char_letter_code + short_emo[i]] = ''
    img_dict[char_letter_code + 'I'] = f'hide {char_img_name} with dissolve'
    return img_dict

# Populates and returns a dict of emotion:image statement. If given an img_dict, will append or update as needed
def populate_img_dict(imgs,img_dict = {}):
    for emo_list in imgs.values(): # 'B': Dict of all emotions of that character
        for emo in emo_list: # For each dict contain emotions for the character
            img_dict[emo] = emo_list[emo]
    return img_dict

def main():
    emotions = ['angry','angry2','angry3','close','cry','curious','dead','embarrass','fear','fear2','happy','happy2','happy3','judge','laugh','lust','lust2','lust3','lust4','normal','sad','sad2','sad3','smirk','surprise','think']
    short_emo = ['A','AA','AAA','Z','U','C','D','E','F','FF','H','HH','HHH','J','Y','L','LL','LLL','LLLL','','S','SS','SSS','M','P','T']
    blank_emotions = ['' for i in range(len(emotions))]
    imgs_katey = {
        'M': get_char_img_dict('katey brown','M',emotions,short_emo),
        'A': get_char_img_dict('athena knight','A',emotions,short_emo),
        'C': get_char_img_dict('athena casual','C',emotions,short_emo),
        'B': get_char_img_dict('katey black','B',emotions,short_emo),
        'G': get_char_img_dict('"Gerald"','G',blank_emotions,short_emo,True),
        'Q': get_char_img_dict('"Queen"','Q',blank_emotions,short_emo,True),
        'H': get_char_img_dict('"Hearld"','H',blank_emotions,short_emo,True),
        'K': get_char_img_dict('katey brown','K',emotions,short_emo),
    }
    
    chars_katey = {
        'A': 'athenaC',
        'M': 'kateyC',
        'C': 'athenaC',
        'B': 'kateyC',
        'G': 'geraldC',
        'K': 'kateyC',
    }

    # Change to change xaligns
    s68_1080 = {
        0:[],
        1:['0.5'],
        2:['0.8','0.2'],
        3:['0.9','0.5','0.15'],
        4:['1.0','0.6','0.3','-0.05'],
        5:['1.15','0.8','0.5','0.2','-0.1']    
    }

    o080_1080 = {
        0:[],
        1:['0.5'],
        2:['0.9','0.0'],
        3:['1.1','0.4','-0.2'],
        4:['1.2','0.7','0.2','-0.3'],
        5:['1.3','0.8','0.3','-0.1','-0.4']
    }
    
    markers: dict[str,str] = {
        'SCENE':'<S>',
        'MENU':'<M>',
        'MENU_END': '</M>',
        'CHOICE': '<C>',
        'CHOICE_END':'</C>',
        'PYTHON':'<PYTHON>',
        'EMPTY': '<>'
    }
    
    align_dict = s68_1080
    sample_f = './dialogue.txt'
    
    # CHANGE these 2 for speakers and imgs to use
    imgs = imgs_katey
    char_dict = chars_katey
            
    img_dict = populate_img_dict(imgs)
    # print('IMAGE DICT:',img_dict,'\n')
    dm = DialogueManager(fn=sample_f,img_dict=img_dict,char_dict=char_dict,logging=True)
    fn = './output.txt'
    
    valid = dm.validate()
    print(f'Full len: {len(dm)}, narration: {len([i for i in dm if i.type == 'NARR'])}, character: {len([i for i in dm if i.type == 'CHAR' and i.char not in dm.MARKERS.values()])}')
    # valid = False
    # print(valid)
    nar_pre_say = ''

    if valid:
        dm.logging = False
        s = dm.gen_renpy(fn,base_aligns=align_dict,markers=markers,limit=500,nar_pre_say=nar_pre_say,triple=False)
        for k,v in s.items():
            if k != 'return_string':
                print('Key',k,'Value',v)