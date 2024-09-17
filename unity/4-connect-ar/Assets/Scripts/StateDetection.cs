using System.Collections;
using System.Collections.Generic;
using System.Linq;
using OpenCvSharp;
using UnityEngine;


public class StateDetection
{
    private bool debugDetection = false;

    private int rows = 6;
    private int cols = 7;

    public int id_red = 1;
    public int id_yellow = -1;

    // color spaces
    // red
    private OpenCvSharp.Scalar lower_red_1;
    private OpenCvSharp.Scalar higher_red_1;
    private OpenCvSharp.Scalar lower_red_2;
    private OpenCvSharp.Scalar higher_red_2;
    // yellow
    private OpenCvSharp.Scalar lower_yellow;
    private OpenCvSharp.Scalar higher_yellow;
    // blue
    private OpenCvSharp.Scalar lower_blue;
    private OpenCvSharp.Scalar higher_blue;

    public StateDetection()
    {
        lower_red_1 = new OpenCvSharp.Scalar(0, 40, 30);
        higher_red_1 = new OpenCvSharp.Scalar(10, 255, 255);
        lower_red_2 = new OpenCvSharp.Scalar(160, 40, 30);
        higher_red_2 = new OpenCvSharp.Scalar(200, 255, 255);
        lower_yellow = new OpenCvSharp.Scalar(20, 60, 30);
        higher_yellow = new OpenCvSharp.Scalar(80, 255, 255);
        // old
        //lower_blue = new OpenCvSharp.Scalar(100, 149, 0);
        //higher_blue = new OpenCvSharp.Scalar(140, 255, 255);
        lower_blue = new OpenCvSharp.Scalar(60, 180, 0);
        higher_blue = new OpenCvSharp.Scalar(160, 255, 255);
    }

    public StateDetection(bool DebugDetection) : this()
    {
        this.debugDetection = DebugDetection;
    }

    public StateResult detectState(Mat frame)
    {
        // Image Preprocessing
        Mat[] preproccessed;
        Mat cImg = new Mat();

        imagePreprocessing(frame, out preproccessed, out cImg);

        int[] board_coords;
        List<OpenCvSharp.Rect> rect_list;
        List<int[]> position_list;

        // setup lists of holedata
        setupListsNew(preproccessed, out rect_list, out position_list, out board_coords);
        //setupLists(preproccessed, out contour_list, out rect_list, out position_list);

        if (position_list.Count > 0)
        {
            bool stateDetected = getState(rect_list, position_list, frame, out StateResult result);
            result.HolesFound = position_list.Count;
            result.boardX = board_coords[0];
            result.boardY = board_coords[1];
            if (debugDetection)
            {
                result.Frame = preproccessed[preproccessed.Length-1];
            }
            else
            {
                foreach(Mat img in preproccessed)
                {
                    img.Dispose();
                }
                cImg.Dispose();
            }
            
            if (stateDetected)
            {
                result.isValid = isValid(result);

                Debug.Log("State ist " + result.isValid);
                return result;
            }
            else
            {
                Debug.Log("getState war false");
                result.isValid = false;
                return result;
            }
        }
        else
        {
            Debug.Log("Positionlist war leer");
            StateResult result = new StateResult();
            result.isValid = false;
            return result;
        }
    }

    // imagepreprocessing for board detection
    private void imagePreprocessing(Mat FrameIn, out Mat[] OutFrames, out Mat CImg)
    {
        // Frame in HSV-ColorSpace
        Mat hsv = new Mat();
        Cv2.CvtColor(FrameIn, hsv, ColorConversionCodes.BGR2HSV);

        // Mask for Board
        Mat blue_mask = new Mat();
        Cv2.InRange(hsv, lower_blue, higher_blue, blue_mask);
        hsv.Dispose();

        Mat board_only = new Mat();
        Cv2.BitwiseAnd(FrameIn, FrameIn, board_only, blue_mask);
        blue_mask.Dispose();

        Mat board_only_blurred = new Mat();
        Cv2.MedianBlur(board_only, board_only_blurred, 11);
        board_only.Dispose();

        CImg = new Mat();
        Cv2.CvtColor(board_only_blurred, CImg, ColorConversionCodes.RGB2GRAY);
        board_only_blurred.Dispose();

        Mat thresh = new Mat();
        Cv2.Threshold(CImg, thresh, 0, 255, ThresholdTypes.BinaryInv | ThresholdTypes.Otsu);


        OutFrames = new Mat[10];
        for(int i = 0; i < 10; i++)
        {
            Mat kernel = Cv2.GetStructuringElement(MorphShapes.Rect, new Size(25-2*i, 3));
            Mat FrameOut = new Mat();

            Cv2.Erode(thresh, FrameOut, kernel);
            OutFrames[i] = FrameOut;
            kernel.Dispose();
        }
        thresh.Dispose();

        //Cv2.Erode(thresh, FrameOut, kernel, null, 1);
    } 

    private void setupListsNew(Mat[] preproccessed, out List<OpenCvSharp.Rect> rect_list, out List<int[]> position_list, out int[] board_coords)
    {
        rect_list = new List<OpenCvSharp.Rect>();
        position_list = new List<int[]>();
        board_coords = new int[2];

        // möglicherweise unnötig
        // Point[][] contours;
        // HierarchyIndex[] hierarchyIndexes;

        Mat labels = new Mat();
        Mat stats = new Mat();
        Mat centroids = new Mat();

        int img_index = 1;
        foreach (Mat img in preproccessed)
        {
            rect_list = new List<OpenCvSharp.Rect>();
            position_list = new List<int[]>();
            board_coords = new int[2];

            int num_labels = Cv2.ConnectedComponentsWithStats(img, labels, stats, centroids, PixelConnectivity.Connectivity8, MatType.CV_32S);

            int count_circles = 0;
            int left_c = 1000;
            int right_c = 0;
            int top_c = 1000;
            int bottom_c = 0;

            for (int i = 0; i < num_labels; i++)
            {
                if (stats.At<int>(i, 4) < 1000)
                {
                    count_circles += 1;
                    //OpenCvSharp.Rect rect = Cv2.BoundingRect(labels[i]);
                
                    int x_rect = stats.At<int>(i, 0);
                    int y_rect = stats.At<int>(i, 1);
                    int x_center_rect = (int)centroids.At<double>(i, 0);
                    int y_center_rect = (int)centroids.At<double>(i, 1); ;
                    int w_rect = stats.At<int>(i, 2);
                    int h_rect = stats.At<int>(i, 3);
                    int area_rect = w_rect * h_rect;

                    OpenCvSharp.Rect rect = new OpenCvSharp.Rect(x_rect, y_rect, w_rect, h_rect);

                    position_list.Add(new int[] { x_center_rect, y_center_rect });
                    rect_list.Add(rect);

                    //only needed if with houghcircles
                    if (left_c >= (int)centroids.At<double>(i, 0))
                    {
                        left_c = (int)centroids.At<double>(i, 0);
                    }
                    if (right_c >= (int)centroids.At<double>(i, 0))
                    {
                        right_c = (int)centroids.At<double>(i, 0);
                    }
                    if (top_c >= (int)centroids.At<double>(i, 1))
                    {
                        top_c = (int)centroids.At<double>(i, 1);
                    }
                    if (bottom_c >= (int)centroids.At<double>(i, 1))
                    {
                        bottom_c = (int)centroids.At<double>(i, 1);
                    }
                }
            }

            board_coords[0] = right_c;
            board_coords[1] = bottom_c;

            if(count_circles == 42)
            {
                Debug.Log("Found all Circles in Img " + img_index);
                return;
            }

            img_index++;
        }
    }

    // get current playstate
    private bool getState(List<OpenCvSharp.Rect> rect_list, List<int[]> position_list, Mat frame, out StateResult result)
    {
        // Frame in HSV-ColorSpace
        result = new StateResult();

        Mat hsv = new Mat();
        Cv2.CvtColor(frame, hsv, ColorConversionCodes.BGR2HSV);

        double mean_w = 0;
        double mean_h = 0;

        foreach (OpenCvSharp.Rect rect in rect_list)
        {
            mean_w += rect.Width;
            mean_h += rect.Height;
        }

        mean_w = mean_w / rect_list.Count;
        mean_h = mean_h / rect_list.Count;

        result.MeanChipSize = (int) mean_w;

        // red chips
        Mat mask1 = new Mat();
        Cv2.InRange(hsv, lower_red_1, higher_red_1, mask1);

        Mat mask2 = new Mat();
        Cv2.InRange(hsv, lower_red_2, higher_red_2, mask2);

        Mat mask_red = new Mat();
        mask_red = mask1 + mask2;
        mask1.Dispose();
        mask2.Dispose();

        Mat img_red = new Mat();
        Cv2.BitwiseAnd(frame, frame, img_red, mask_red);

        img_red.Dispose();

        // yellow chips
        Mat mask_yellow = new Mat();
        Cv2.InRange(hsv, lower_yellow, higher_yellow, mask_yellow);
        hsv.Dispose();

        Mat img_yellow = new Mat();
        Cv2.BitwiseAnd(frame, frame, img_yellow, mask_yellow);
        //result.Frame = img_yellow;
        //img_yellow.Dispose();

        Debug.Log(position_list.Count);

        if (position_list.Count == 42)
        {
            position_list.Sort((x, y) => x[0].CompareTo(y[0]));

            List<List<int[]>> sorted_position_list_tmp = new List<List<int[]>>();
            for (int i = 0; i < 7; i++)
            {
                List<int[]> row = new List<int[]>();
                for (int j = 0; j < 6; j++)
                {
                    row.Add(position_list[i * 6 + j]);
                }
                sorted_position_list_tmp.Add(row);
            }
            List<int[]> sorted_position_list = new List<int[]>();

            foreach (List<int[]> item in sorted_position_list_tmp)
            {
                item.Sort((x, y) => x[1].CompareTo(y[1]));
                foreach (int[] position in item)
                {
                    sorted_position_list.Add(position);
                }
            }

            int x_i = 0;
            int y_i = 0;
            bool isFirstRow = true;

            for (int i = 0; i < sorted_position_list.Count; i++)
            {
                int x = (int)sorted_position_list[i][0];
                int y = (int)sorted_position_list[i][1];
                int r = (int)((mean_h + mean_w) / 5);

                Mat img_grid_circle = Mat.Zeros(new Size(frame.Width, frame.Height), MatType.CV_8UC1);
                Cv2.Circle(img_grid_circle, x, y, r, new OpenCvSharp.Scalar(255, 255, 255), -1);

                Mat img_res_red = new Mat();
                Cv2.BitwiseAnd(img_grid_circle, img_grid_circle, img_res_red, mask_red);

                Mat img_res_yellow = new Mat();
                Cv2.BitwiseAnd(img_grid_circle, img_grid_circle, img_res_yellow, mask_yellow);

                if (Cv2.CountNonZero(img_res_red) > 0)
                {
                    result.State[x_i, rows - y_i - 1] = id_red;
                    result.CountRedChips += 1;
                }
                else if (Cv2.CountNonZero(img_res_yellow) > 0)
                {
                    result.State[x_i, rows - y_i - 1] = id_yellow;
                    result.CountYellowChips += 1;
                }

                result.HoleCoords[x_i, rows - y_i - 1] = new int[] { x, y };

                img_grid_circle.Dispose();
                img_res_red.Dispose();
                img_res_yellow.Dispose();

                if (isFirstRow)
                {
                    result.ColCoords[x_i] = new int[] { x, (result.HoleCoords[x_i, 5][1] - (int)mean_h * 2) };
                }

                isFirstRow = false;
                y_i++;
                if (y_i == 6)
                {
                    y_i = 0;
                    x_i++;
                    isFirstRow = true;
                }
            }

            mask_red.Dispose();
            mask_yellow.Dispose();

            if (result.ColCoords.Any(x => x == null))
            {
                Debug.Log("ColCoords hat Null Wert");
                return false;
            }

            return true;
        }
        else
        {
            Debug.Log("Nicht genug Löcher gefunden");
        }
        return false;
    }

    // check ob unter chip noch löcher sind "Floating Chip"
    private bool isValid(StateResult result)
    {
        for(int i = 0; i < 7; i++)
        {
            bool chipFound = false;
            for(int j = 0; j < 6; j++)
            {
                if(chipFound && result.State[i,j] != 0)
                {
                    return false;
                }
                chipFound = result.State[i, j] == 0;
            }
        }

        return true;
    }
}
