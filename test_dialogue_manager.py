# TODO: Fix all tests from the changes made recently
import pytest, tempfile,os
from dialogue_manager import DialogueManager
from dialogue import Dialogue
class TestDialogueManager:
    
    @pytest.fixture()
    def sample(self):
        return '''Some people talking.

AC
They're not home? I don't know anything about that.

M
Hm...

MH
Well, in any case, we have you! Want to help look and get the gang together? We could have a picnic at the hangout spot! It'd be nice to chat with everyone after what happened.

AH
Okay, yeah. I have everything I'll need.

The end!'''

    @pytest.fixture()
    def dm(self,sample):
        return DialogueManager(sample,logging=False)
        
    def test_setup_bytes(self,sample):
        assert len(DialogueManager(sample.encode()).full_dialogue) == 6
        
    def test_setup_string(self,sample):
        assert len(DialogueManager(sample).full_dialogue) == 6
        
    def test_setup_filename(self,sample):
        # Not making it delete auto since method requires a path string rather than the io object
        temp = tempfile.NamedTemporaryFile('wb+',dir='./',delete=False)
        try:
            temp.write(sample.encode())
            fn = temp.name
            temp.close()
            assert len(DialogueManager(fn).full_dialogue) > 0
        finally:
            os.remove(os.path.join('./',fn))
        
    def test_validate_success(self,dm):
        assert dm.validate() == True
        
    def test_invalid_format_no_two_newlines(self):
        sample = 'Test narration\n\nChar 1\nHi\nNarration without 2 preceding \\n'
        assert DialogueManager(sample,logging=False).validate() == False
    
    def test_invalid_format_tab_character(self):
        sample = 'Test narration\n\n\tChar 1\nHi\nNarration without 2 preceding \\n'
        assert DialogueManager(sample,logging=False).validate() == False
        
    def test_get_dialogue_by_index(self,dm: DialogueManager):
        assert dm[0].text == 'Some people talking.'
        
    def test_get_dialogue_index_oob(self,dm: DialogueManager):
        with pytest.raises(IndexError):
            dm[99]
    
    def test_add_dialogue(self,dm: DialogueManager):
        new_dialogue = Dialogue(Dialogue.CHARACTER_TYPE,'char','This is character')
        dm.add_dialogue(new_dialogue)
        assert len(dm.full_dialogue) == 7
        assert isinstance(dm.full_dialogue[6][0], Dialogue) and dm.full_dialogue[6][1] == len(dm.full_dialogue) - 1

    def test_change_dialogue(self,dm: DialogueManager):
        # Change a given dialogue by index to a different dialogue
        diag = Dialogue('type','char','text')
        dm.change_dialogue(diag,0)
        changed_diag = dm.full_dialogue[0][0]
        assert changed_diag.type == 'type' and changed_diag.char == 'char' and changed_diag.text == 'text'

    def test_insert_dialogue(self,dm:DialogueManager):
        dialogue = Dialogue('t','c','CharText')
        boolean = dm.insert_dialogue(dialogue,2)
        assert boolean
        assert len(dm) == 7
        assert dm[2] == dialogue
        assert dm.full_dialogue[2][1] == 2 and dm.full_dialogue[3][1] == 3
        
    def test_fail_insert_dialogue_too_high(self,dm:DialogueManager):
        boolean = dm.insert_dialogue(Dialogue(),99)
        assert not boolean
    
    def test_insert_dialogues_limited_text(self,dm: DialogueManager):
        class FakeDialogue(Dialogue):
            def get_limited_sentences(self, limit):
                return ['Test. This test. How to test.','Sometimes when we test we break things.','...ok? ...']
        dm.full_dialogue[2][0] = FakeDialogue('t','c','Test. This test. How to test. Sometimes when we test we break things. ...ok? ...')
        dm.limit_dialogue(2,limit = 0)
        assert len(dm) == 8
        assert dm[2].text == 'Test. This test. How to test.'
        assert dm[3].text == 'Sometimes when we test we break things.'
        assert dm[4].text == '...ok? ...'
        assert dm[5].text == "Well, in any case, we have you! Want to help look and get the gang together? We could have a picnic at the hangout spot! It'd be nice to chat with everyone after what happened."
    
    def test_remove_dialogue(self,dm:DialogueManager):
        diag = dm.remove_dialogue(1)
        assert len(dm) == 5
        assert dm[1].text == 'Hm...'
        assert dm.full_dialogue[1][1] == 1 and dm.full_dialogue[2][1] == 2
        assert diag.text == "They're not home? I don't know anything about that."
        
    def test_fail_remove_dialogue_empty(self):
        dm = DialogueManager()
        assert not dm.remove_dialogue(0)
    
    def test_remove_dialogue_no_exist(self,dm:DialogueManager):
        assert not dm.remove_dialogue(99)
    
    def test_find_dialogue_by_type(self,dm:DialogueManager):
        # Get all dialogues that have a given type
        diags = dm.find_dialogue_by_type(Dialogue.NARRATION_TYPE)
        assert len(diags) == 2
        for d in diags:
            assert d.type == Dialogue.NARRATION_TYPE
    
    def test_find_dialogue_by_char(self,dm:DialogueManager):
        # Get all dialogues that have a given char
        diags = dm.find_dialogue_by_char('M')
        assert len(diags) == 2 and diags[0].char == 'M' and diags[1].char == 'MH'
    
    def test_find_dialogue_by_text(self,dm:DialogueManager):
        # Get all dialogues that have given text or part of it
        diags = dm.find_dialogue_by_text('?')
        assert len(diags) == 2
        assert diags[0].char == 'AC' and diags[1].char == 'MH'
    
    # TODO: Use parameters?
    @pytest.mark.parametrize('index,result',[
        (1,'"""Test.\n\nAnother box.\n\nYet another!"""'),
        (0,'"""A\nHi."""'),
        (2,'"""M\nAnother box.\n\nYet another!'),
        (4,'A\nAll done.\n\nI said I was done.'),
        (6,'Narration.\n\nMore narration.\n\nFinal.')
    ])
    def get_triple_from_single_quote(self,index,result):
        dm = DialogueManager('A\nHi.\n\nM\nTest.\n\nM\nAnother box.\n\nM\nYet another!\n\nA\nAll done.\n\nA\nI said I was done.\n\nNarration.\n\nMore narration.\n\nFinal.',logging=False)
        ret = dm.get_triple_from_single_quote(1)[0]
        assert ret.text == '"""Test.\n\nAnother box.\n\nYet another!"""'