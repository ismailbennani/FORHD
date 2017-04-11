#include "opencv2/core/core.hpp"
#include "opencv2/highgui/highgui.hpp"
#include "opencv2/face.hpp"

#include <iostream>
#include <string>
#include <functional>
#include <cstdio>

#include <dirent.h>
#include <stdio.h>
#define BOOST_NO_CXX11_SCOPED_ENUMS
#include <boost/filesystem.hpp>
#undef BOOST_NO_CXX11_SCOPED_ENUMS

using namespace std;
using namespace cv;

const string MODELFILEPATH = "models/";
const string MODELFILENAME = "lbphfacerecognizer.xml";
const string FULLPATH = MODELFILEPATH + MODELFILENAME;

const string IMGSFILEPATH = "imgs/faces/";

inline bool fileExists (const string& name) {
    if (FILE *file = fopen(name.c_str(), "r")) {
        fclose(file);
        return true;
    } else {
        return false;
    }
}

int create_directory(const string &dirpath) {
  boost::filesystem::path dir(dirpath);
  if(!boost::filesystem::create_directories(dir)) {
      cout << endl << "Couldn't create " << dirpath << endl;
      return 0;
  }
  return 1;
}

void applyToFileNames(DIR *dir, function<void(struct dirent*)> func){
  struct dirent *ent;
  while ((ent = readdir (dir)) != NULL) {
    func(ent);
  }
}

void retrieveKnownPeople(vector<string> *knownPeopleName) {
  DIR *dir;

  if ((dir = opendir(IMGSFILEPATH.c_str())) != NULL) {
    applyToFileNames(dir, [&knownPeopleName](struct dirent *ent){
      if (strcmp(ent->d_name, ".") != 0 && strcmp(ent->d_name, "..") != 0) {
        knownPeopleName->push_back(ent->d_name);
      }
    });
    closedir (dir);
  } else {
    if(!create_directory(IMGSFILEPATH)){
      perror ("create_directory");
      exit(1);
    }
  }
}

int makeStringLabelDicts(Ptr<cv::face::LBPHFaceRecognizer> faceRecognizer,
                          vector<string> *knownPeopleNames,
                          map<int, string> *labelToName,
                          map<string, int> *nameToLabel) {
  int highestLabel = 0;
  int i = 0;
  string s;
  for(i = 0; i < knownPeopleNames->size(); ++i)
  {
    s = knownPeopleNames->at(i);
    vector<int> label = faceRecognizer->getLabelsByString(s);
    labelToName->insert(pair<int, string>(label[0], s));
    nameToLabel->insert(pair<string, int>(s, label[0]));
    if(label[0] > highestLabel){
      highestLabel = label[0];
   }
  }

  return highestLabel;
}

string getNextAvailableFilename(string &dirPath) {
  int i = 0;
  while(true){
    char* path = (char*)malloc(1024);
    sprintf(path, "%s%d.jpg", dirPath.c_str(), i);
    if(fileExists(path)){
      ++i;
    } else {
      return path;
    }
  }
}

void makeImgVec(string &s, vector<Mat> *imgVec, vector<int> *labels, int i){
  DIR *dir;
  if ((dir = opendir((IMGSFILEPATH+s).c_str())) != NULL) {
    applyToFileNames(dir, [imgVec, labels, i, &s](struct dirent *ent){
      if (strcmp(ent->d_name, ".") != 0 && strcmp(ent->d_name, "..") != 0) {
        char* path = (char*)malloc(1024);
        sprintf(path, "%s%s/%s", IMGSFILEPATH.c_str(), s.c_str(), ent->d_name);
        Mat img = imread(path,  IMREAD_GRAYSCALE);
        if (img.data != NULL){
          imgVec->push_back(img);
          labels->push_back(i);
        } else {
          cout << endl << "Failed to load image " << path << ", skipping.";
        }
      }
    });
  } else {
    perror("opendir");
    exit(1);
  }
}

int main(int argc, char** argv){
  // Parseing arguments

  int i;
  bool dontsave = false;
  for(i = 0; i < argc; ++i){
    if (strcmp(argv[i], "-reset") == 0){
      printf("RESET:TRUE\n");
      remove((MODELFILEPATH+MODELFILENAME).c_str());
    } else if (strcmp(argv[i], "-dontsave") == 0){
      printf("DONTSAVE:TRUE\n");
      dontsave = true;
    }
  }


  cout << "-- Opencv version: " << CV_VERSION << endl;
  cout << "-- Initializing face recognition" << endl;
  Ptr<cv::face::LBPHFaceRecognizer> faceRecognizer = cv::face::createLBPHFaceRecognizer();

  cout << "Retrieving known people .." << flush;
  vector<string> knownPeopleNames;
  retrieveKnownPeople(&knownPeopleNames);
  cout << " Done" << endl;

  if(fileExists(FULLPATH)){
    cout << "-- Loading pre-trained model .." << flush;
    String path;
    path = FULLPATH.c_str();
    faceRecognizer->load(path);
    cout << " Done" << endl;
  } else {
    cout << "-- Creating and training new model .." << endl;
    vector<Mat> imgVec;
    vector<int> labels;
    int i; string s;
    cout << "Loading images .." << flush;
    for(i = 0; i < knownPeopleNames.size(); ++i){
      s = knownPeopleNames[i];
      makeImgVec(s, &imgVec, &labels, i);

      faceRecognizer->setLabelInfo(i, s);
    }
    cout << " Done" << endl;
    cout << "Training model .." << flush;
    faceRecognizer->train(imgVec, labels);
    cout << " Done" << endl;
  }

  cout << "Creating label<->name correspondance .." << flush;
  map<int, string> labelToName;
  map<string, int> nameToLabel;
  int highestLabel = makeStringLabelDicts(faceRecognizer,
                                          &knownPeopleNames,
                                          &labelToName,
                                          &nameToLabel);
  cout << " Done" << endl;

  cout << "Ready to go" << endl;
  while(true){
    string imgpath;

    cout << "Enter a path";
    cin >> imgpath;

    if (strcmp(imgpath.c_str(), "Stop") == 0){
      break;
    }

    Mat img = imread(imgpath, IMREAD_GRAYSCALE);
    if(!img.data){
      cout << "Couldn't load " << imgpath << endl;
      continue;
    }

    int prediction = faceRecognizer->predict(img);

    if(prediction == -1){
      string person_name;

      cout << "Coudln't recognize this person, give me their name" << flush;
      cin >> person_name;

      int label;

      if(find(knownPeopleNames.begin(), knownPeopleNames.end(), person_name) != knownPeopleNames.end()) {
        label = nameToLabel[person_name];
      } else {
        label = highestLabel + 1;
        labelToName.insert(pair<int, string>(label, person_name));
        nameToLabel.insert(pair<string, int>(person_name, label));
        ++highestLabel;


      }
      faceRecognizer->update(vector<Mat>(1, img), vector<int>(1, label));
      faceRecognizer->setLabelInfo(label, person_name);

      string dirpath = IMGSFILEPATH+person_name+"/";
      string newFilePath = getNextAvailableFilename(dirpath);

      imwrite(newFilePath, img);
    } else {
      printf("I know you! You are: %s\n", labelToName[prediction].c_str());
    }
  }
  if(!dontsave){
    if (!fileExists(FULLPATH)){
      FILE *f = fopen(FULLPATH.c_str(), "w+");
      fclose(f);
    }
    String path;
    path = FULLPATH.c_str();
    faceRecognizer->save(path);
  }
}
