import uuid
import os
import streamlit as st
from PIL import Image
from time import sleep
from streamlit_extras.app_logo import add_logo

from llm import initialize_model
from imageGen import *

# Creating API Authentication functions
def auth():    
    os.environ['OPENAI_API_KEY'] = st.session_state.openai_api_key
    os.environ['STABILITY_KEY'] = st.session_state.dreamstudio_api_key
    
    st.session_state.genreBox_state = False
    st.session_state.apiBox_state = True

  
# Basic Page Configurations
st.set_page_config(
    page_title='StoryBook GPT',
    page_icon=Image.open('icons/fairytale.png'),
    layout='wide',
    menu_items={
        'About': "StoryGPT is an interactive storybook experience using ChatGPT and Midjourney"
    },
    initial_sidebar_state='expanded'
)

st.title(f"📖 StoryGPT")

# Creating Session States
if 'cols' not in st.session_state:
    st.session_state['cols'] = []
if 'keep_graphics' not in st.session_state:
    st.session_state['keep_graphics'] = False
if 'data_dict' not in st.session_state:
    st.session_state['data_dict'] = {}
if 'genreBox_state' not in st.session_state:
    st.session_state['genreBox_state'] = True
if 'apiBox_state' not in st.session_state:
    st.session_state['apiBox_state'] = False
if 'openai_api_key' not in st.session_state:
    st.session_state['openai_api_key'] = ''
if 'dreamstudio_api_key' not in st.session_state:
    st.session_state['dreamstudio_api_key'] = ''
if 'genre_input' not in st.session_state:
    st.session_state['genre_input'] = 'Use a random theme'

# Configuring the Sidebar
with st.sidebar:
    st.image('icons/no bg logo.png')
    
    st.markdown('''
    This is an interactive storybook experience built using ChatGPT and Stable Diffusion.
    ''')
    
    with st.expander('Instructions'):
        st.markdown('''
        - To begin StoryGPT, please enter your own OpenAI API key, and the Dreamstudio API key.
        - After entering the API keys, please enter the genre/theme of your desired story, and watch the magic unfold.
        ''')
    
    # Sidebar Form, wherein the user enters their API Keys. [Completed]
    with st.form(key='API Keys'):
        openai_key = st.text_input(
            label='Your OpenAI API Key', 
            key='openai_api_key',
            type='password',
            disabled=st.session_state.apiBox_state,
            help='You can create your own OpenAI API key by going to https://platform.openai.com/account/api-keys (Sign up required)'
        )
        dreamstudio_key = st.text_input(
            label='Your Stability.AI API Key', 
            key='dreamstudio_api_key',
            type='password',
            disabled=st.session_state.apiBox_state,
            help='You can create your own Stability.AI API key by going to https://beta.dreamstudio.ai/account (Sign up required)'
        )
        
        btn = st.form_submit_button(label='Begin StoryGPT!', on_click=auth)

    st.info('**Note:** You can close the sidebar when you enter the API keys')

# Displaying the API Key warnings
if not openai_key.startswith('sk-'): 
    st.warning('Please enter your OpenAI API Key to start StoryGPT', icon='⚠')
if not dreamstudio_key.startswith('sk-'):
    st.warning('Please enter your Stability.AI API Key to start StoryGPT', icon='⚠')


# Defining the functions for the actual screen
def get_story_and_image(user_resp):
    # Setting the models to get the story
    llm_model = initialize_model()
    sd_model = stability_setup()
        
    # Getting, and parsing through the responses received from the LLM
    bot_response = llm_model.predict(input=user_resp)
    print(bot_response)
    response_list = bot_response.split("\n")
                       
    responses = list(filter(lambda x: x != '' and x != '-- -- --', response_list))
    
    if len(response_list) != 1:
        img_prompt = response_list[-1]
        sd_img = generate_image(sd_model, img_prompt, (192, 192))
    else:
        sd_img = None
        
    responses = list(filter(lambda x: 'Stable Diffusion' not in x and 'Image prompt' not in x, responses))
    
    opts = []
    story = ''
    label = ''
    for response in responses:
        response = response.strip()  
        if response.startswith('What') or response.startswith('Which') or response.startswith('Choose'):
            label = '**' + response + '**'
        elif response[1] == '.' or response[1] == ')' or response[1:4] == ' --' or response.startswith('Option'):
            opts.append(response) 
        else:
            story += response + '\n'  
    
    return {
        'Story': story,
        'Radio Label': label,
        'Options': opts,
        'Image': sd_img
    }
    
    
@st.cache_data(experimental_allow_widgets=True, show_spinner='Generating your story...')
def get_output(_pos: st.empty, el_id='', genre=''):
    st.session_state.keep_graphics = True
    
    if el_id:        
        st.session_state['genreBox_state'] = True
        st.session_state[f'expanded_{el_id}'] = False
        st.session_state[f'radio_{el_id}_disabled'] = True
        st.session_state[f'submit_{el_id}_disabled'] = True

        user_choice = st.session_state[f'radio_{el_id}']
    
    if genre:         
        st.session_state['genreBox_state'] = False
        user_choice = genre
    
    with _pos:    
        data = get_story_and_image(user_choice)
        add_new_data(data['Story'], data['Radio Label'], data['Options'], data['Image'])
    
    
def generate_content(story, lbl_text, opts: list, img, el_id):
    if f'expanded_{el_id}' not in st.session_state:
        st.session_state[f'expanded_{el_id}'] = True
    if f'radio_{el_id}_disabled' not in st.session_state:
        st.session_state[f'radio_{el_id}_disabled'] = False
    if f'submit_{el_id}_disabled' not in st.session_state:
        st.session_state[f'submit_{el_id}_disabled'] = False
    
    story_pt = list(st.session_state["data_dict"].keys()).index(el_id) + 1
    expander = st.expander(f'Part {story_pt}', expanded=st.session_state[f'expanded_{el_id}'])   
    col1, col2 = expander.columns([0.65, 0.35])
    empty = st.empty()
    if img:
        col2.image(img, width=40, use_column_width='always')
    
    with col1:
        st.write(story)
        
        if lbl_text and opts:
            with st.form(key=f'user_choice_{el_id}'): 
                st.radio(lbl_text, opts, disabled=st.session_state[f'radio_{el_id}_disabled'], key=f'radio_{el_id}')
                st.form_submit_button(
                    label="Let's move on!", 
                    disabled=st.session_state[f'submit_{el_id}_disabled'], 
                    on_click=get_output, args=[empty], kwargs={'el_id': el_id}
                )


def add_new_data(*data):
    '''
    Arguments to be mentioned:
        - Text (the main story)
        - Text (the label for the radio group)
        - Options to be displayed (in the radio group)
        - Image to be displayed (in the size 256x256)
    '''
    el_id = str(uuid.uuid4())
    st.session_state['cols'].append(el_id)
    st.session_state['data_dict'][el_id] = data
    
# Genre Input widgets
with st.container():
    col_1, col_2, col_3 = st.columns([8, 1, 1], gap='small')
    
    col_1.text_input(
        label='Enter the theme/genre of your story',
        key='genre_input',
        placeholder='Enter the theme of which you want the story to be', 
        disabled=st.session_state.genreBox_state
    )
    col_2.write('')
    col_2.write('')
    col_2_cols = col_2.columns([0.5, 6, 0.5])
    col_2_cols[1].button(
        ':arrows_counterclockwise: &nbsp; Clear', 
        key='clear_btn',
        on_click=lambda: setattr(st.session_state, "genre_input", ''),
        disabled=st.session_state.genreBox_state
    )
    col_3.write('')
    col_3.write('')
    begin = col_3.button(
        'Begin story →',
        on_click=get_output, args=[st.empty()], kwargs={'genre': st.session_state.genre_input},
        disabled=st.session_state.genreBox_state
    )
    
for col in st.session_state['cols']:
    data = st.session_state['data_dict'][col]
    generate_content(data[0], data[1], data[2], data[3], col)
