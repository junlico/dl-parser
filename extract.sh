#!/bin/bash

declare -A FILES
DOWNLOADS_DIR="$HOME/Downloads"
MONO_DIR="Monos"
SAVE_DIR="$HOME/Documents/deno/files"

FILES=(
  ["TextLabel"]="en"
  ["TextLabelJP"]="ja"
  ["AbilityData"]="ability"
  ["CharaData"]="chara"
  ["WeaponData"]="weapon"
  ["DragonData"]="dragon"
  ["AmuletData"]="amulet"
  ["SkillData"]="skill"
  ["SkillChainData"]="skillChain"
)

function most_recent_zip() {
  # get most recent zip path in DOWNLOADS_DIR
  local file="$(ls -t $DOWNLOADS_DIR/*.zip | head -n1)"
  echo "$file"
}

function clean_file() {
  # clean file, remove blank & junk data
  # $1 save_path
  echo "Save: $1"

  local regex=''
  # remove all lines before match /Element data/
  regex+='/Element data/,$!d;'
  # remove all lines contains [\d+]
  regex+='/\[[0-9]+\]/d;'
  # remove all lines after match /_Id = 0|_Id = ""/
  regex+='/_Id = 0|_Id = ""/,$d;'

  # sed -r "$regex" $1 | sed '1d' >$2
  sed -r "$regex" | sed '1d' >$1
}

function extract_file_and_clean() {
  # $1 zip_path
  # $2 file_path inside zip, relative path
  # $3 save_path
  unzip -c "$1" "$2" | clean_file $3
}

function unzip_files() {
  zip_file=$(most_recent_zip)

  for file in "${!FILES[@]}"; do
    mono_path="$MONO_DIR/$file.txt"
    save_path="$SAVE_DIR/${FILES[$file]}.txt"
    extract_file_and_clean "$zip_file" "$mono_path" "$save_path"
  done
}

unzip_files
