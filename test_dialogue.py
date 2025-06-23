# TODO: Fix all tests from the changes recently
from dialogue import Dialogue
from effect import Effect
import pytest

class TestDialogue:
    
    @pytest.fixture
    def dialogue(self):
        return Dialogue(Dialogue.NARRATION_TYPE,Dialogue.NARRATION_CHAR,'Text for dialogue.')
    
    def test_change_text(self,dialogue: Dialogue):
        dialogue.change_main_prop(text='Changed text')
        assert dialogue.text == 'Changed text'
        
    def test_change_char(self,dialogue: Dialogue):
        dialogue.change_main_prop(char='Changed char')
        assert dialogue.char == 'Changed char'
        
    def test_change_type(self,dialogue: Dialogue):
        dialogue.change_main_prop(d_type='Changed type')
        assert dialogue.type == 'Changed type'
    
    def test_add_effect(self,dialogue):
        dialogue.add_effect(Effect())
        assert len(dialogue.effects) == 1 and isinstance(dialogue.effects[0],Effect)
    
    def test_null(self,dialogue):
        dialogue.null()
        assert dialogue.type == '' and dialogue.char == '' and dialogue.text == ''
        
    @pytest.mark.parametrize('dialogue,result',[
        (Dialogue('t','c','This is text.'),'This is text.'),
        (Dialogue('t','c','This is text?'),'This is text?'),
        (Dialogue('t','c','This is text!'),'This is text!'),
        (Dialogue('t','c','This is text!?'),'This is text!?'),
        (Dialogue('t','c','This text has a space at the end. '),'This text has a space at the end.'),
        (Dialogue('t','c','This is text!!!?!?!'),'This is text!!!?!?!'),
        (Dialogue('t','c','This is text...'),'This is text...'),
        (Dialogue('t','c','This is text...!'),'This is text...!'),
        (Dialogue('t','c','This is text...?'),'This is text...?'),
        (Dialogue('t','c','...this is text...?'),'...this is text...?'),
        (Dialogue('t','c','...this is text with no punc'),'...this is text with no punc'),
        (Dialogue('t','c','This is text. That was one sentence. Should only return the first.'),'This is text.'),
        (Dialogue('t','c','This is text? That was one sentence. Should only return the first.'),'This is text?'),
        (Dialogue('t','c','This is text! That was one sentence. Should only return the first.'),'This is text!'),
        (Dialogue('t','c','This is text?!! That was one sentence. Should only return the first.'),'This is text?!!'),
        (Dialogue('t','c','This is text!! That was one sentence. Should only return the first.'),'This is text!!'),
        (Dialogue('t','c','This is text... That was one sentence. Should only return the first.'),'This is text...'),
        (Dialogue('t','c','This is text...this is one sentence. Should only return the first.'),'This is text...this is one sentence.'),
    ])
    def test_get_first_sentence(self,dialogue,result):
        assert dialogue.get_first_sentence() == result
        
    def test_get_sentences(self):
        test_str = 'This is a sentence.||This is another!||This is yet another?||What?!||No...!||How could this be!?||This sentence...is just 1 sentence.||This one however...||Well, these are 2.||2!'
        class FakeDialogue(Dialogue):
            sentences = test_str.split('||')
            def get_first_sentence(self):
                return FakeDialogue.sentences.pop(0)
        d = FakeDialogue('t','c',test_str.replace('||',' '))
        sentences = d.get_sentences()
        assert len(sentences) == 10
        assert sentences[0] == 'This is a sentence.' and sentences[-1] == '2!'
        
    def test_get_sentences_same(self):
        d = Dialogue('t','c',"Test. Test. Test. Test.")
        sentences = d.get_sentences()
        assert len(sentences) == 4
        assert sentences[0] == 'Test.' and sentences[-1] == 'Test.'
        
    @pytest.mark.parametrize('limit,result',[
        (0,['This is a sentence. This is testing the limit function to determine how much text to allow into a given item in the returning list. Should the limit be too low, the limit will be the longest sentence here. Okay?']),
        (170,['This is a sentence. This is testing the limit function to determine how much text to allow into a given item in the returning list.', 'Should the limit be too low, the limit will be the longest sentence here. Okay?']),
        (234,['This is a sentence. This is testing the limit function to determine how much text to allow into a given item in the returning list. Should the limit be too low, the limit will be the longest sentence here. Okay?']),
        (900,['This is a sentence. This is testing the limit function to determine how much text to allow into a given item in the returning list. Should the limit be too low, the limit will be the longest sentence here. Okay?']),
        (210,['This is a sentence. This is testing the limit function to determine how much text to allow into a given item in the returning list. Should the limit be too low, the limit will be the longest sentence here.', 'Okay?']),
        (211,['This is a sentence. This is testing the limit function to determine how much text to allow into a given item in the returning list. Should the limit be too low, the limit will be the longest sentence here. Okay?']),
        (212,['This is a sentence. This is testing the limit function to determine how much text to allow into a given item in the returning list. Should the limit be too low, the limit will be the longest sentence here. Okay?']),
    ])
    def test_limit_text(self,limit,result):
        class FakeDialogue(Dialogue):
            def get_sentences(self):
                return ['This is a sentence.','This is testing the limit function to determine how much text to allow into a given item in the returning list.','Should the limit be too low, the limit will be the longest sentence here.','Okay?']
        d = FakeDialogue('t','c','This is a sentence. This is testing the limit function to determine how much text to allow into a given item in the returning list. Should the limit be too low, the limit will be the longest sentence here. Okay?')
        test = d.get_limited_sentences(limit)
        assert test == result
        
    def test_equal_no_text(self):
        d1 = Dialogue('t','c','Test text.')
        d2 = Dialogue('t','c','Different text, same everything else.')
        assert d1.equal_no_text(d2)
        