from dialogue_manager import DialogueManager, Dialogue
class RenpyGen:
    def __init__(self, dm: DialogueManager):
        self.dialogue_manager = dm
    
    def get_triple_quoted_text(self,index: int,add_newline = True,full_dialogue = None):
        '''
        Gets the dialogue at index, and any subsequent ones with same char.
        Returns tuple (string, diag_count) which will be >= 1.
        '''
        newline = ''
        if add_newline:
            newline = '\n'
        diag = full_dialogue[index][0]
        # How to start the string and what each iteration adds
        start_str = '"""\n' + diag.text + '\n'
        repeat_str = '\n' + '<text>' + '\n'
        if diag.type == Dialogue.CHARACTER_TYPE:
            start_str = diag.char + ' ' + '"""\n' + diag.text + '\n'
        result_str = start_str
        
        i = index + 1
        while i < len(full_dialogue) and full_dialogue[i][0].char == diag.char:
            new_diag = full_dialogue[i][0]
            result_str += repeat_str.replace('<text>',new_diag.text)
            i += 1
        result_str += '"""' + newline
        return (result_str,i - index)
    
    def handle_dialogue_v2_helper(self,index: int, triple = False, add_newline = True, full_dialogue = None):
        if full_dialogue[index][0].type == Dialogue.NARRATION_TYPE:
            return self.handle_narration_v2_helper(index,triple,add_newline,full_dialogue)
        return self.handle_character_v2_helper(index,triple,add_newline,full_dialogue)
    
    def handle_narration_v2_helper(self,index: int,triple = False, add_newline = True, full_dialogue = None):
        newline = ''
        if add_newline:
            newline = '\n'
        diag = full_dialogue[index][0]
        if diag.type != Dialogue.NARRATION_TYPE:
            print(f'Index {index} does not point to narration. Char: {diag.char} Text: {diag.text}')
            return ('',0)
        if not triple:
            # print(f'"Index: {index} Result: {(diag.text,1)}')
            return (f"'{diag.text}'{newline}",1)
        # Triple quote
        return self.get_triple_quoted_text(index,add_newline,full_dialogue)

        
    def handle_character_v2_helper(self,index: int, triple = False, add_newline = True,full_dialogue = None):
        newline = ''
        if add_newline:
            newline = '\n'
        diag = full_dialogue[index][0]
        if diag.type != Dialogue.CHARACTER_TYPE:
            print(f'Index {index} does not point to character. Char: {diag.char} Text: {diag.text}')
            return ('',0)
        if not triple:
            return (f"{diag.char} '{diag.text}'{newline}",1)
        # Triple quote
        return self.get_triple_quoted_text(index,add_newline,full_dialogue)
    
    # When menu is found, make a full dialogue obj from menu start to menu end
    # If there are any nested, put those in too.
    # Then make code for the menu with indentation.
    def start_menu(self,index,full_dialogue: list[list[Dialogue]]):
        menus = self.get_menus(index,full_dialogue)
        indent = 1
        result_str = 'menu ' + full_dialogue[0][0].text + ':\n'
        # Create start for menu
        for i in menus:
            diag = i[0]
            result_str += '\t'* indent + ''
            if diag.char == DialogueManager.MARKERS.get('MENU'):
                indent += 1
            
    
    # Given index of a menu, and diag list from that menu on,
    # get all menus until the end. If it encounters another menu during, run function again
    # Return list.
    def get_menus(self,index,full_dialogue: list[list[Dialogue]]):
        start_d = full_dialogue[0][0]
        print(f'=== Start Menu index: {index}, char: {start_d.char}, text: {start_d.text} ===')
        print('Length of full dialogue given: ' + str(len(full_dialogue)))
        print('Length of absolute full diag: ' + str(len(self.dialogue_manager.full_dialogue)))
        menu_dialogues: list[list[Dialogue]] = [full_dialogue[0]]
        # Add every diag into new list from index of menu to index of ending menu
        for i in range(1,len(full_dialogue)):
            # if full_dialogue[i][0].char == DialogueManager.MARKERS.get('MENU'):
                # return self.get_menus(i,full_dialogue)
            menu_dialogues.append(full_dialogue[i])
            if full_dialogue[i][0].char == DialogueManager.MARKERS.get('MENU_END'):
                break
        end_m = menu_dialogues[len(menu_dialogues)-1]
        end_d = end_m[0]
        print(f'=== End Menu index: {self.dialogue_manager.full_dialogue.index(end_m)}, char: {end_d.char}, text: {end_d.text} ===')
        return menu_dialogues
    # When encounter a menu, get full dialouge = beginning and end of menu.
    # When encounter a choice, get full dialouge = beginning and end of choice.
    # Menu will contain everything and can be ran into the generator.
    # Choice will only contain that code, and can be ran into generator
    
    def special_marker_router(self,index: int, full_dialogue = None):
        full_dialogue = full_dialogue or self.dialogue_manager.full_dialogue
        markers = self.dialogue_manager.MARKERS
        diag = full_dialogue[index][0]
        if diag.char == markers.get('MENU'):
            self.start_menu(index,full_dialogue[index:])
        
    def gen_renpy_v2(self,triple: bool = False,add_newline = True, full_dialogue = None):
        # print(self.char_dict)
        '''
        Version 2, trying to be simpler. First design inefficient, then increase over time.
        1. If narration, quotes around. If char, inlcude the char and space
        TODO Allow this function to be called within itself using a separate full dialogue variable.
        Allow choices to be a thing, as each choice is a branch that invokes another full generation up to end of choice
        
        Pass in a full dialogue, using that in the recursive calls? Or create a new DialogueManager with all dialogue
        from the start to end of block, calling it's gen?
        
        '''
        full_dialogue = full_dialogue or self.dialogue_manager.full_dialogue
        if not full_dialogue or len(full_dialogue) <= 0:
            return ''
        result_code = ''
        i = 0
        while i < len(full_dialogue):
            diag = full_dialogue[i][0]
            # If character in marker list, handle it. Unfinished currently
            if diag.char in self.dialogue_manager.MARKERS.values():
                self.special_marker_router(i,full_dialogue)
            (diag_result_code,skip_count) = self.handle_dialogue_v2_helper(i,triple,add_newline,full_dialogue)
            result_code += diag_result_code
            # Skip ahead x amount of lines and end iteration early
            if skip_count > 0:
                i += skip_count
                continue
            # Failsafe, shouldn't ever happen
            i += 1
            print("Shouldn't have incremented i here. i after increment = " + str(i))
        print('Result:\n' + result_code)