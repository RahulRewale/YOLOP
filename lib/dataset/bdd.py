import numpy as np
import json

from .AutoDriveDataset import AutoDriveDataset
from .convert import convert, id_dict, id_dict_single
from tqdm import tqdm


class BddDataset(AutoDriveDataset):
    def __init__(self, cfg, is_train, inputsize, transform=None):
        super().__init__(cfg, is_train, inputsize, transform)
        # create a list of dictionaries, each containing (image path, detections, drivable area mask path, lanelines mask path)
        self.cfg = cfg
        self.single_cls = cfg.single_det_class  # detect only one class of objects
        self.db = self._get_db()

    def _get_db(self):
        """
        get database from the annotation file

        Inputs:

        Returns:
        gt_db: (list)database   [a,b,c,...]
                a: (dictionary){'image':, 'information':, ......}
        image: image path
        mask: path of the segmetation label
        label: [cls_id, center_x//256, center_y//256, w//256, h//256] 256=IMAGE_SIZE
        """
        print('building database...')
        gt_db = []
        height, width = self.shapes
        for mask in tqdm(list(self.mask_list)):
            mask_path = str(mask)
            label_path = mask_path.replace(str(self.mask_root), str(self.label_root)).replace(".png", ".json")
            image_path = mask_path.replace(str(self.mask_root), str(self.img_root)).replace(".png", ".jpg")
            lane_path = mask_path.replace(str(self.mask_root), str(self.lane_root))
            with open(label_path, 'r') as f:
                label = json.load(f)
            data = label['frames'][0]['objects']
            data = self.filter_data(data)           # if single_class=True, detect only the classes in id_dict_single
            # (class id, center x, center y, w, h)  # coordinates are normalized w.r.t to image dimensions
            gt = np.zeros((len(data), 5))

            for idx, obj in enumerate(data):
                category = obj['category']
                # replace traffic light class with four classes - tl_red, tl_green, tl_yellow, tl_none
                if category == "traffic light":
                    color = obj['attributes']['trafficLightColor']
                    category = "tl_" + color
                
                # process only if one of the recognized classes; ignore unrecognized classes
                if category in id_dict.keys():
                    x1 = float(obj['box2d']['x1'])
                    y1 = float(obj['box2d']['y1'])
                    x2 = float(obj['box2d']['x2'])
                    y2 = float(obj['box2d']['y2'])
                    cls_id = id_dict[category]
                    # if you have multiple classes in id_dict_single, all of them get merged/mapped to class id 0    
                    if self.single_cls:
                         cls_id = 0
                    gt[idx][0] = cls_id
                    # normalized coordinates for center x, center y, box width, and box height
                    box = convert((width, height), (x1, x2, y1, y2))
                    gt[idx][1:] = list(box)
                
            rec = [{
                'image': image_path,
                'label': gt,
                'mask': mask_path,
                'lane': lane_path
            }]

            gt_db += rec
        print('database build finish')
        return gt_db

    def filter_data(self, data):
        remain = []
        for obj in data:
            if 'box2d' in obj.keys():  # obj.has_key('box2d'):
                if self.single_cls:
                    if obj['category'] in id_dict_single.keys():    # detect only the classes in id_dict_single
                        remain.append(obj)
                else:
                    remain.append(obj)
        return remain

    def evaluate(self, cfg, preds, output_dir, *args, **kwargs):
        """  
        """
        pass
