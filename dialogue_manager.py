from dialogue import Dialogue
import re,utils
import copy
# Parse and get all dialogue in format
# 
# Char
# CharText

# Narration

# Narration

# Char
# CharText

# Char
# CharText

# ...

# Keeps the order and returns a list of lists, the first being the dialogue and second being the index/position.
# In the event of narration, the character is some constant for easy identifying
# The character is whatever line preceded their text, can modify later
# This class is no different from just having a list of Dialogue objects. It offers a way to keep things ordered and validate
# char_dict can be used to identify characters, offering a script-to-custom replacement (for example, A becomes Abigail in the character). If provided, the rest of the character becomes emotion
# Emotion can be used for img or any purpose
# TO DO: Modify to allow taking 2 regexs for character and narration and setting up based on them. Also change validation to be dynamic in this way
class DialogueManager:
    MARKERS: dict[str,str] = {
        'SCENE':'<S>',
        'MENU':'<M>',
        'MENU_END': '</M>',
        'CHOICE': '<C>',
        'CHOICE_END':'</C>',
        'PYTHON':'<PYTHON>',
        'EMPTY': '<>'
    }
    # Given some bytes, string or file, create a manager of dialogue. Priority is bytes, string and then file
    # It is assumed that full_dialogue will always have the second item be a number pertaining to its order, and that no number is skipped in the full list (nothing like 1,2,4,5 etc)
    def __init__(self,byte_data: bytes = b'', str_data = '',fn: str = '',logging: bool = True, char_dict: dict[str,str] = None, img_dict: dict[str,str] = None):
        self.full_dialogue: list[list[Dialogue,int]] = []
        self.original_byte_data = byte_data or b''
        self.original_lines: str = ""
        self.logging = logging
        self.char_dict = char_dict or {}
        self.img_dict = img_dict or {}
        if byte_data or str_data or fn:
            self.setup_dialogue(byte_data or str_data or fn)
    
    # Just to log things
    def log(self,text):
        if self.logging:
            print(text)
    
    # Given either bytes, a string, or a file name, get the byte data to use for dialogue. Attempts to auto detect input as either bytes, string or a filename (which itself is a string)
    def get_data(self,data: bytes | str = None):
        if data:
            if not isinstance(data,bytes):
                return utils.get_byte_data(data)
            return data
    
    # Proper decoding and removing \r
    @staticmethod
    def decode_bytes(byte_data: bytes):
        return byte_data.decode().replace('\r','')
    
    # Given the raw char from the lines used to setup, return the character and emotion if the character exists, else return nothing
    def get_diag_aspects(self,raw_char: str) -> tuple[str,str] | None:
        # Check each char to be in dict. If none, leave as is. If so, divide aspects and set dialogue properties as such
        # If it's just one char, no need to do anything.
        if not raw_char:
            return None
        if len(raw_char) == 1:
            return (raw_char,'')
        
        # For each char in the character given, if the next char plus the total chars before is still found in the character dictionary, keep going
        char_str = ''
        key_list = list(self.char_dict.keys())
        for c in raw_char:
            if char_str + c in key_list:
                char_str += c
            else:
                break
        str_len = len(char_str)
        if str_len > 0:
            char = raw_char[:str_len]
            emo = raw_char[str_len:]
            return (char,emo)
        return None

    # Helper to split responsibility
    def handle_special_chars_gen_renpy_helper(self,d: Dialogue,markers: dict,indent_base = 4,state: dict = None):
        return_string = ''
        return_dict = {}
        indent = state.get('indent') or 0
        if d.char == markers.get('SCENE'):
            self.log('Scene change: ' + d.text)
            return_dict['hidden'] = set()
            return_dict['prev_diags'] = {}
            scene = d.text.replace(markers.get('SCENE'),'').split('|')
            if len(scene) < 2:
                self.log(f"Couldn't parse scene. Scene gotten: {scene}, dialogue for reference: {d.__dict__}")
            else:
                return_string += ' '*indent_base*indent + 'scene ' + scene[0] + ' with ' + scene[1] + '\n'
        # For choices, since they are branches, we need to save previous game state. Once a choice ends, we revert to that state
        # This is mainly for show/hide and align statements. Otherwise each choice, when generated, will also be setting up state
        # Maybe just call the gen code again with all dialogues up to the end of the choice? We can give it our current state
        # That way, once the gen is finished, we back back up the stack to here with our original state.
        # In that branch, their state was modified. How to use their state? In a nested choice maybe?
        # So we get here with choice between A and B, choose A, then we gen code up until end of choice A
        # However in there we reach choice AA and AB. So there we hit AB, then do the gen code for diags all through close of AB
        # Now the state of A is still from right before choice AB, so we resume as normal with state A.
        # Once done with that choice, our state is now...original. But a choice should be able to alter state?
        # The final state should always be the end of the choices we made.
        
        # A or B. For A, gen code. Now we come back (original state). For B, gen code. Now we come back (original state)
        # But what state are we using? Whichever the user chooses...but what is that?
        elif d.char == markers.get('MENU'):
            self.log('Menu added. Name: ' + d.text)
            if d.text and d.text != markers.get('EMPTY'):
                return_string += ' '*indent_base*indent + 'menu ' + d.text.replace(' ','') + ':\n'
            else:
                return_string += ' '*indent_base*indent + 'menu:\n'
            return_dict['indent'] = indent + 1
        elif d.char == markers.get('CHOICE'):
            # If we have a choice, need to generate all the next stuff with the current state?
            self.log('Choice added. Choice: ' + d.text)
            return_string += ' '*indent_base*indent + '"' + d.text + '":' + '\n'
            return_dict['indent'] = indent + 1
        elif d.char == markers.get('CHOICE_END') or d.char == markers.get('MENU_END'):
            self.log('Choice or menu removed. Char: ' + d.char)
            return_dict['indent'] = indent - 1
        elif d.char == markers.get('PYTHON'):
            self.log('Python code added.')
            return_string += ' '*indent_base*indent + d.text + '\n'
        return_dict['return_string'] = return_string
        return return_dict
    
    # Generate renpy code based on all available info. Optimize to not do duplicate/unecessary statements. Currently a naive implementation. If write_file, will attempt to write there
    # indent_base controls how many spaces are considered an indent (renpy doesn't like the \t char)
    # Limit can be used to ensure text doesn't overflow. Default is 200 characters
    # If triple, will triple quote all speech and text. BUG currently with voice as it will do one voice for the entire lines if the original line was limited.
    # If pre_say, will put this statement before each say like if you wanted to do a voice or something. Could have pre_say be python function call that would do something
    # TODO: Implement a way to handle menus and choices. Store separate state, recursively calling for each choice? How will we know the choice that was selected to determine the state to resume at?
    def gen_renpy(
        self,write_file: str = None,
        indent_base = 4,
        limit = 200,
        pre_say = 'voice get_sound()\n',
        triple = False,
        markers = None,
        diags: list[list[Dialogue,int]] = [],
        state: dict = None,nar_pre_say='', 
        base_aligns = {
            0:[],
            1:['0.5'],
            2:['0.9','0.0'],
            3:['1.1','0.4','-0.2'],
            4:['1.2','0.7','0.2','-0.3'],
            5:['1.3','0.8','0.3','-0.1','-0.4']
        }) -> dict:
        
        if diags and len(diags) == 0 or len(self.full_dialogue) == 0:
            self.log('No dialogue to use to generate.')
            return {}
        # Everything pertaining to a state will be stored in a dictionary. At any time we can remember the "state" of a scene and return if need be.
        # This includes all hidden characters, previously/currently shown, code indentation and other variables
        # By passing it in, we can create aribtrary states to then parse the dialogue with!
        # This can be used for returning to before a choice was picked or jumping to a particular label
        state = state or {}
        
        # Establish all vars from state given
        
        # Our ever growing string containing all the code.
        return_string = state.get('return_string') or ''
        
        # Every dialogue we've previously encountered while iterating
        prev_diags: dict[str,Dialogue] = state.get('prev_diags') or {}
        
        # A set of characters that have been hidden via the hide command
        hidden = state.get('hidden') or set()
        
        # Special character markers for additional functionality
        markers = markers or DialogueManager.MARKERS
        
        # A copy to reset all dialogue at the end so as not to distrub the data structure
        temp_full_dialogue = copy.deepcopy(self.full_dialogue)

        # Our current indent. Mainly for conditionals, choices, etc.
        indent = state.get('indent') or 0
        
        # How many characters are on screen at start
        chars_on_screen = state.get('chars_on_screen') or 0
        
        # How many characters are on screen after processing
        new_chars_on_screen = state.get('new_chars_on_screen') or 0
        
        # Which dialogues to use when creating code, defaults to whatever dialogue we set up
        self.full_dialogue = copy.deepcopy(diags) if diags else self.full_dialogue
        
        # Execute everything here in a try so that, in case something goes wrong, the full dialogue remains intact
        try:
            # First, set up dialogue
            i = 0
            while i < len(self.full_dialogue):
                self.limit_dialogue(i,limit)
                i += 1
            
            # Now that length has possibly changed, do another pass to enquote as needed
            if not triple:
                for i in range(len(self.full_dialogue)):
                    d = self.full_dialogue[i][0]
                    if d.char not in markers.values():
                        self.dequote(i)
                        d.text = d.text.replace('"','\\"').replace("'","\\'").replace('%','\%')
                        self.enquote(i)
            else:
                i = 0
                while i < len(self.full_dialogue):
                    d = self.full_dialogue[i][0]
                    if d.char not in markers.values():
                        d.text = d.text.replace('"','\\"').replace("'","\\'")
                        d.triple_into_single_quote(i)
                i += 1
            
            # Next, if we are on a character, determine the img statement to use. This includes whether to use a hide.
            # If we have already shown the same img, no need to. If we've already hidden, no need to
            # Handle every marker separately, skipping the rest of execution if needed
            # A scene change resets all display info
            # Afterwards, adjust xaligns as needed (involving multiple show statements), display img, and finally do say statement
            index = 0
            while index < len(self.full_dialogue):
                # Get the dialogue in order as defined by the list of [diag,index] rather than iteration count
                i: int = self.full_dialogue[index][1]
                d: Dialogue = self.full_dialogue[i][0]
                prev_d: Dialogue = self.full_dialogue[i-1][0] if i > 0 else None
                # # If before we had a choice, use the current state when generating future code for that choice
                # if prev_d and prev_d.char == markers.get('CHOICE'):
                    # Generate code for the choice, and store the state after that choice.
                    # In the case of nested choices, will keep using the previous state
                    # new_state = self.gen_renpy(indent_base=indent_base,limit=limit,pre_say=pre_say,triple=triple,markers=markers,state=state, diags = diags[index:])
                    # When done with that choice and we come back, skip the dialogues that the choice handled
                    # index += 1
                    # continue
                if d.type == Dialogue.CHARACTER_TYPE:
                    if d.char in markers.values():
                        # Vital that the name of the returning dict's keys match the state dict's keys
                        results = self.handle_special_chars_gen_renpy_helper(d,markers,indent_base,state)
                        for k in results:
                            state[k] = results[k]
                        hidden = state.get('hidden',{})
                        prev_diags = state.get('prev_diags',{})
                        return_string += state.get('return_string','')
                        indent = state.get('indent',indent)
                        index += 1
                        continue
                        
                    chars_on_screen = len([key for key in prev_diags if prev_diags[key].img and not prev_diags[key].img.startswith('hide')])
                    
                    # If we are doing a menu, don't do anything with imgs, just simply have a say statement
                    if prev_d and prev_d.char != markers.get('MENU'):
                        # Handle everything with images, pre-says, etc...
                        img = d.img
                        if img:
                            # What is the character used in the show? EX: show char char_normal
                            img_char = img.split(' ')[1]
                        prev_char_diag = prev_diags.get(d.char)
                        # When you change an img/hide, you need to update everyone's aligns only if they need to be updated.
                        # If prev_imgs length changes, we added or removed someone. To check for removes, make a list = prev_imgs where img doesn't start with 'hide'
                        # On that list, if the length of it is different from the previously recorded length, update aligns.
                        # Note that aligns iterate sequentially, so the order you insert characters matter. Our way is first one moves right
                        
                        # If the img is hidden/was last hidden, don't bother even setting up prev diag or adding a hide statement
                        if img and img.startswith('hide') and (d.char in hidden or prev_diags.get(d.char) is None):
                            img = ''
                        # No previous and have img
                        elif not prev_char_diag and img:
                            prev_diags[d.char] = d
                            hidden.discard(d.char)
                        elif prev_char_diag:
                            # img and previous img were same or the character is hidden
                            if prev_char_diag.img == img or d.char in hidden:
                                img = ''
                            # img and previous were different
                            elif prev_char_diag.img != img:
                                prev_diags[d.char] = d
                        
                        # Remove if we have a hide now and had a prev
                        if prev_char_diag and img and img.startswith('hide'):
                            hidden.add(d.char)
                            prev_diags.pop(d.char)
                            return_string += ' '*indent_base*indent + 'hide ' + img_char + ' with dissolve\n'
                        
                        # Update aligns for everyone if chars on screen changed
                        new_chars_on_screen = len([key for key in prev_diags if prev_diags[key].img and not prev_diags[key].img.startswith('hide')])
                        if chars_on_screen != new_chars_on_screen:
                            # Go through each char on screen, setting its alignment based on amount of people.
                            # Because of the way we add items to prev_imgs, the first character will move towards the right with others coming in from the left
                            # Need to ensure character lines up
                            align_list = base_aligns[new_chars_on_screen]
                            logging_s = ''
                            for i in range(len(align_list)):
                                # We know there are no hide statements here. However, if we are on our current char and there was an img to show, combine them
                                key = list(prev_diags.keys())[i]
                                p_diag = prev_diags[key]
                                align = align_list[i]
                                p_diag.xalign = align
                                return_string += ' '*indent_base*indent
                                # If there were no characters before, don't do the linear
                                if chars_on_screen == 0:
                                    trans = 'xalign ' + align
                                else:
                                    trans = 'linear 0.3 xalign ' + align
                                # Determine show statement, if any. If we hide, no need to show that with an align
                                # If current char's img is not = to previous dialogue img of that particular char (may or may not be the same as our current one)
                                # Then just do a show, no need to redisplay the same img
                                if img != p_diag.img:
                                    return_string += 'show ' + p_diag.img.split(' ')[1] + ':\n' + ' '*indent_base*(indent+1) + trans + '\n'
                                else:
                                    return_string += p_diag.img + ':\n' + ' '*indent_base*(indent+1) + trans + '\n'
                                logging_s += 'New align: ' + key + ' - Value: ' + align + ' || '
                            # self.log(logging_s)
                        # This elif handles if you didn't update xaligns (no new or disappearing chars) but still changed an image
                        elif img:
                                return_string += ' '*indent_base*indent + img + '\n'
                        if pre_say:
                                return_string += ' '*indent_base*indent + pre_say
                    return_string += ' '*indent_base*indent + d.char + ' ' + d.text + '\n'
                     
                elif d.type == Dialogue.NARRATION_TYPE:
                    # self.log('Narration: ' + d.text[0:100] + '...')
                    # Determine what to put into the code
                    if nar_pre_say:
                        return_string += ' '*indent_base*indent + nar_pre_say
                    return_string += ' '*indent_base*indent + d.text + '\n'
                # Update state
                state.update({
                    'return_string':return_string,
                    'indent':indent,
                    'hidden':hidden,
                    'prev_diags':prev_diags,
                    'chars_on_screen':chars_on_screen,
                    'new_chars_on_screen':new_chars_on_screen
                })
                index += 1
                
            self.log('Visible chars on script end: ' + str(new_chars_on_screen))   
            if write_file:
                with open(write_file,'wb') as file:
                    file.write(return_string.encode())
        finally:
            diags = copy.deepcopy(temp_full_dialogue)
        if indent != 0:
            self.log('Something went wrong during generating. Final indent should be 0, but was ' + str(indent) + ' instead. Possibly did not end a choice or menu properly. Double check code output.')
        return state

    # If creating instance without param constructor, at some point call this to setup instance properties.
    def setup_dialogue(self,byte_data: bytes):
        if not byte_data:
            self.log('Setup Error: input received was empty.')
            return None
        byte_data = self.get_data(byte_data)
        # Define regex for character dialogue and narration
        dialogue_pattern = r"^(.+)\n(.+)"
        narration_pattern = r"^(?!.+\n).+"
        self.original_byte_data = byte_data
        self.original_lines = DialogueManager.decode_bytes(byte_data)
        lines = self.original_lines.split('\n')
        i = 0
        
        # For storing the order of dialogue
        dialogue_index = 0
        
        while i < len(lines):
            line = lines[i].replace('\t','').strip()
            
            # Check for dialogue (character + speech)
            matcher = map(lambda x: x.replace('\t','').strip(),lines[i:i+2])
            char_match = re.match(dialogue_pattern, "\n".join(matcher))
            if char_match:
                char, speech = char_match.groups()
                dialogue = Dialogue(Dialogue.CHARACTER_TYPE,char,speech)
                dialogue.raw_char = char
                # If the character is in the list, separate aspects of it
                aspects = self.get_diag_aspects(char)
                if aspects:
                    dialogue.char = self.char_dict.get(aspects[0],char)
                    dialogue.emotion = aspects[1] or None
                    dialogue.img = self.img_dict.get(aspects[0] + aspects[1],None)
                    
                self.full_dialogue.append([dialogue,dialogue_index])
                i += 2  # Skip the next line as it's part of the dialogue
                dialogue_index += 1
            # Check for narration
            elif re.match(narration_pattern, line):
                dialogue = Dialogue(Dialogue.NARRATION_TYPE,Dialogue.NARRATION_CHAR,line)
                self.full_dialogue.append([dialogue,dialogue_index])
                i += 1
                dialogue_index += 1
            else:
                self.log(f'Line was skipped. line: {line}')
                i += 1  # Skip any unmatched lines

    # Validate this instance, that is, the parsed dialogue and narration can be reconstructed into its original setup (Currently only one format)
    def validate(self):
        invalid = False
        if not self.original_lines and len(self.full_dialogue) == 0:
            self.log('Validation Info: No original lines stored and no full dialogue. Valid, but was it setup correctly?')
            invalid = True
        elif len(self.full_dialogue) == 0:
            self.log('Validation Error: No dialogue stored but there are bytes to check against. Check that setup was done properly.')
            invalid = True
            
        blocks = self.full_dialogue

        # Reconstructing
        reconstructed_lines = ''
            
        # Print the blocks
        for i in range(len(blocks)):
            if invalid:
                break
            dialogue = blocks[i][0]
            # self.log(f"Block {blocks[i][1]}: Type: {dialogue.type}, Char: {dialogue.char}, Text: {dialogue.text}")
            reconstructed_lines += f"{dialogue.raw_char}\n{dialogue.text}" if dialogue.type == Dialogue.CHARACTER_TYPE else dialogue.text
            if i != len(blocks) - 1:
                reconstructed_lines += '\n\n'
            # Give helpful error
            if not self.original_lines.startswith(reconstructed_lines):
                self.log(f'Validation Error: Error at iteration {i}. Printing dialogue items from {i - 2} or 0 to {i + 2} or up to end of list')
                start = max(i - 2,0)
                end = min(i+3,len(blocks))
                for j in range(start,end):
                    self.log(blocks[j][0].__dict__)
                invalid = True
        # self.log(f'\nReconstructed Text:\n{reconstructed_lines}')
        if reconstructed_lines:
            self.log(f'Valid? {reconstructed_lines == self.original_lines}')
        elif invalid:
            self.log('Validation Error: Could not reconstruct text.')
        else:
            self.log('Validation Info: Something went wrong. It seemed to be valid but did not generate any reconstructed lines.')
        return reconstructed_lines == self.original_lines

    # Return list of "say" statements
    def get_say_statements(self) -> list[str]:
        return [str(i[0]) for i in self.full_dialogue]
    
    # Append to end of list
    def add_dialogue(self,dialogue: Dialogue):
        index = len(self.full_dialogue)
        self.full_dialogue.append((dialogue,index))
        
    # Change a given dialogue, index based    
    def change_dialogue(self,dialogue: Dialogue,index):
        self.full_dialogue[index][0] = dialogue
        
    # Insert a dialogue at a given index, shifting others to the right (after)
    def insert_dialogue(self,dialogue: Dialogue,index) -> bool:
        if index >= len(self.full_dialogue):
            self.log('Given index was greater than length of list. Did you mean to simply add instead via add_dialogue?')
            return False
        self.full_dialogue[index:index] = [[dialogue,index]]
        # Adjust all to the right
        for i in range(index + 1,len(self.full_dialogue)):
            self.full_dialogue[i][1] += 1
        return True
    
    # Given some index, will limit the dialogue text, insertinig multiple dialogues with everything being the same besides text to the right/sequentially
    def limit_dialogue(self,index: int,limit: int = 0):
        dialogue = self.full_dialogue[index][0]
        sentences = dialogue.get_limited_sentences(limit)
        # Don't adjust if it didn't limit
        if len(sentences) <= 1:
            return
        self.remove_dialogue(index)
        for sen in reversed(sentences):
            # Make a new dialogue with the limited sentences, keep all old qualities but change text. Then insert
            new_dialogue = copy.deepcopy(dialogue)
            new_dialogue.text = sen
            self.insert_dialogue(new_dialogue,index)
            
    # Given some index, will look forward for all dialogues with the same features besides text. Returns a Dialogue whose text is triple quoted, each separate diag text separated by \n\n
    # Returns tuple (Dialogue,iterations) where iterations = amount of dialogues added
    def get_triple_from_single_quote(self,index: int) -> tuple[Dialogue,int]:
        if index >= len(self.full_dialogue):
            self.log(f'Attempted to start at index {index} but dialogue list length is {len(self.full_dialogue)}.')
            return ()
        count = 0
        # Base dialogue to compare everything to
        base_dialogue = self.full_dialogue[index][0]
        # Look ahead at each dialogue. If they are the same besides text, then keep the text in our increasing return
        ret = '"""' + base_dialogue.text
        for i in range(index + 1,len(self.full_dialogue) - 1):
            diag = self.full_dialogue[i][0]
            if base_dialogue.equal_no_text(diag):
                ret += '\n\n' + diag.text
                count += 1
            # We break prematurely to avoid going through the whole dialogue every time
            else:
                break
        ret += '"""'
        # Return a dialogue that is identical besides the text
        return_dialogue = Dialogue()
        return_dialogue.__dict__ = base_dialogue.__dict__
        return_dialogue.text = ret
        return (return_dialogue,count)
    
    # Gets list of single quoted dialogues from a triple quoted one.
    # TODO: Write test
    def get_single_from_triple_quote(self,index: int):
        diag = self.full_dialogue[index][0]
        if diag.text.startswith('"""'):
            texts = diag.text.replace('"""','').split('\n\n')
            return [Dialogue(diag.type,diag.char,t) for t in texts]
        return []

    def enquote(self,index: int):
        diag = self.full_dialogue[index][0]
        if diag.text[0] != '"':
            diag.text = '"' + diag.text + '"'
            
    def dequote(self,index: int):
        diag = self.full_dialogue[index][0]
        if diag.text[0] == '"' and diag.text[-1] == '"':
            diag.text = diag.text[1:len(diag.text) - 1]
    
    # Remove dialogue at a given index, shifting everything to the right of it to the left and returns the dialogue or None
    def remove_dialogue(self,index) -> Dialogue:
        if len(self.full_dialogue) == 0:
            self.log(f'Attempted to remove dialogue at index {index} but empty.')
            return None
        if index >= len(self.full_dialogue):
            self.log(f'Attempted to remove dialogue at index {index} but length is {len(self.full_dialogue)}.')
            return None
        ret = self.full_dialogue[index][0]
        self.full_dialogue = self.full_dialogue[:index] + self.full_dialogue[index+1:]
        # Adjust all to the left
        for i in range(index,len(self.full_dialogue)):
            self.full_dialogue[i][1] -= 1
        return ret
    
    # Replaces a set amount of dialogues with the tirple quote version
    # TODO: Test?
    def single_into_triple_quote(self,index):
        diag,count = self.get_triple_from_single_quote(index)
        self.change_dialogue(diag,index)
        for _ in range(count):
            self.remove_dialogue(index + 1)
            
    # Replaces a triple quote dialgoue with many single quoted versions
    # TODO: Test?
    def triple_into_single_quote(self,index):
        diags = self.get_single_from_triple_quote(index)
        self.remove_dialogue(index)
        for diag in reversed(diags):
            self.insert_dialogue(diag,index)
        
    def find_dialogue_by_type(self,d_type) -> list[Dialogue]:
        return [d for d,_ in self.full_dialogue if d.type.find(d_type) > -1]
    
    def find_dialogue_by_char(self,char) -> list[Dialogue]:
        return [d for d,_ in self.full_dialogue if d.char.find(char) > -1]
    
    def find_dialogue_by_text(self,text) -> list[Dialogue]:
        return [d for d,_ in self.full_dialogue if d.text.find(text) > -1]
    
    # Most common reason for accessing, allows using in iterator contexts. Note that the return is the dialogue itself, not the list of (dialogue,index) since you already have index
    def __getitem__(self,index) -> Dialogue:
        return self.full_dialogue[index][0]
    
    def __len__(self):
        return len(self.full_dialogue)
    
    def __str__(self):
        s = ''
        for d,_ in self.full_dialogue:
            s += d.__str__() + '\n'
        return s