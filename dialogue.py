from effect import Effect
class Dialogue:
    CHARACTER_TYPE = 'CHAR'
    NARRATION_TYPE = 'NARR'
    NARRATION_CHAR = '<NARRCHAR>'
    def __init__(self,type: str = '',char: str = '',text: str = ''):
        self.type = type
        self.char = char
        self.text = text
        self.emotion = ''
        self.img = ''
        self.xalign = ''
        self.effects = []
        self.raw_char = ''
    
    # "Removes" the dialogue, nulling it's attributes
    def null(self):
        self.type = ''
        self.char = ''
        self.text = ''
    
    def add_effect(self,effect: Effect):
        self.effects.append(effect)
    
    # Change the type, char and/or text of a dialogue. Cannot use this to null a field.
    def change_main_prop(self,d_type = '',char = '',text = ''):
        if d_type:
            self.type = d_type
        if char:
            self.char = char
        if text:
            self.text = text
            
    # Find the first sentence in text. Considers "test...this." to be one sentence, and "test... However." to be 2 and will return "test..."
    def get_first_sentence(self):
        text = self.text
        sentence = ''
        endings = ['!','?','.']
        for i,char in enumerate(text):
            sentence += char
            if char in endings:
                # We're done if the char we're at is the last one
                if i+1 == len(text):
                    return sentence
                else:
                    # If the next char is a space, sentence ended.
                    if text[i+1] == ' ':
                        return sentence
        return sentence
            
    # Get a list of sentences from the text.
    def get_sentences(self) -> list[str]:
        # Save for later
        text = self.text
        sentences = []
        try:
            while self.text:
                sen = self.get_first_sentence()
                sentences.append(sen)
                sen_index = self.text.find(sen)
                self.text = self.text[:sen_index] + self.text[sen_index + len(sen):]
                self.text = self.text.strip()
        except:
            print('Something went wrong trying to get length of sentences.')
            raise
        finally:
            # Restore
            self.text = text
        return sentences
    
    # Get a list of sentences from the text limited by some limit. If limit is too small, use the longest sentence length. If limit is <= 0, just get a list of 1 item being the entire line
    def get_limited_sentences(self,limit = 0) -> list[str]:
        if limit <= 0:
            return [' '.join(self.get_sentences())]
        sentences = self.get_sentences()
        items = []
        min_limit = max(map(lambda x : len(x),sentences))
        # Use longest sentence if bad limit given
        if not limit or limit < min_limit:
            limit = min_limit
        # Store current length. If exceed, reset and add new item.
        current_length = 0
        # Store the current item
        current_item = ''
        # Store the ever growing string. Once we reach limit, reset this.
        s = ''
        while len(sentences) > 0:
            current_item = sentences.pop(0) + ' '
            s += current_item
            current_length += len(current_item)
            # If we are at last item, append whatever we have
            if len(sentences) == 0:
                items.append(s.rstrip())
            # Check the next item's length to the current. If it exceeds the limit, append what we have and start fresh.
            elif current_length + len(sentences[0]) > limit:
                items.append(s.rstrip())
                current_item = ''
                s = ''
                current_length = 0
        return items
    
    # Test that a dialogue is equal to mine, disregarding the text
    def equal_no_text(self,diag: 'Dialogue'):
        ret = False
        temp = self.text
        temp2 = diag.text
        self.text = diag.text = ''
        if self.__dict__ == diag.__dict__:
            ret = True
        self.text = temp
        diag.text = temp2
        return ret
    
    # For == comparison
    def __eq__(self, diag: 'Dialogue'):
        return self.__dict__ == diag.__dict__
        
    # Most common way of printing    
    def __str__(self):
        return f'{self.char} "{self.text}"'
    
    # Most common thing to ask about
    def __len__(self):
        return len(self.text)