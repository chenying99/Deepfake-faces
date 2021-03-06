import numpy as np
import dlib
import cv2 as cv
import os
from imutils import face_utils

"""
    This module is not used in the project. 
    But the code from this module is very valuable for me as education material.  
"""


# Read points from text file
def readPoints(path):
    # Create an array of points.
    points = []

    # Read points
    with open(path) as file:
        for line in file:
            x, y = line.split()
            points.append((int(x), int(y)))

    return points


# Apply affine transform calculated using srcTri and dstTri to src and
# output an image of size.
def applyAffineTransform(src, srcTri, dstTri, size):
    # Given a pair of triangles, find the affine transform.
    warpMat = cv.getAffineTransform(np.float32(srcTri), np.float32(dstTri))

    # Apply the Affine Transform just found to the src image
    dst = cv.warpAffine(src, warpMat, (size[0], size[1]), None, flags=cv.INTER_LINEAR,
                        borderMode=cv.BORDER_REFLECT_101)

    return dst


# Check if a point is inside a rectangle
def rectContains(rect, point):
    if point[0] < rect[0]:
        return False
    elif point[1] < rect[1]:
        return False
    elif point[0] > rect[0] + rect[2]:
        return False
    elif point[1] > rect[1] + rect[3]:
        return False
    return True


# Calculate delanauy triangle
def calculateDelaunayTriangles(rect, points):
    # create subdiv
    subdiv = cv.Subdiv2D(rect)

    # Insert points into subdiv
    for p in points:
        k = []

        # There are 4 'if' blocks which exist only like crutch. Shame on me.
        if p[0] >= 200:
            k.append(200 - 1)
            k.append(p[1])
            k = tuple(k)
            p = k

        k = []
        if p[1] >= 200:
            k.append(p[0])
            k.append(200 - 1)
            k = tuple(k)
            p = k

        k = []
        if p[0] < 0:
            k.append(0)
            k.append(p[1])
            k = tuple(k)
            p = k

        k = []
        if p[1] >= 200:
            k.append(p[0])
            k.append(0)
            k = tuple(k)
            p = k

        subdiv.insert(p)

    triangleList = subdiv.getTriangleList()

    delaunayTri = []

    pt = []

    for t in triangleList:
        pt.append((t[0], t[1]))
        pt.append((t[2], t[3]))
        pt.append((t[4], t[5]))

        pt1 = (t[0], t[1])
        pt2 = (t[2], t[3])
        pt3 = (t[4], t[5])

        if rectContains(rect, pt1) and rectContains(rect, pt2) and rectContains(rect, pt3):
            ind = []
            # Get face-points (from 68 face detector) by coordinates
            for j in range(0, 3):
                for k in range(0, len(points)):
                    if (abs(pt[j][0] - points[k][0]) < 1.0 and abs(pt[j][1] - points[k][1]) < 1.0):
                        ind.append(k)
                        # Three points form a triangle. Triangle array corresponds to the file tri.txt in FaceMorph
            if len(ind) == 3:
                delaunayTri.append((ind[0], ind[1], ind[2]))

        pt = []

    return delaunayTri


# Warps and alpha blends triangular regions from img1 and img2 to img
def warpTriangle(img1, img2, t1, t2):
    # Find bounding rectangle for each triangle
    r1 = cv.boundingRect(np.float32([t1]))
    r2 = cv.boundingRect(np.float32([t2]))

    # Offset points by left top corner of the respective rectangles
    t1Rect = []
    t2Rect = []
    t2RectInt = []

    for i in range(0, 3):
        t1Rect.append(((t1[i][0] - r1[0]), (t1[i][1] - r1[1])))
        t2Rect.append(((t2[i][0] - r2[0]), (t2[i][1] - r2[1])))
        t2RectInt.append(((t2[i][0] - r2[0]), (t2[i][1] - r2[1])))

    # Get mask by filling triangle
    mask = np.zeros((r2[3], r2[2], 3), dtype=np.float32)
    cv.fillConvexPoly(mask, np.int32(t2RectInt), (1.0, 1.0, 1.0), 16, 0)

    # Apply warpImage to small rectangular patches
    img1Rect = img1[r1[1]:r1[1] + r1[3], r1[0]:r1[0] + r1[2]]
    # img2Rect = np.zeros((r2[3], r2[2]), dtype = img1Rect.dtype)

    size = (r2[2], r2[3])

    img2Rect = applyAffineTransform(img1Rect, t1Rect, t2Rect, size)

    img2Rect = img2Rect * mask

    # Copy triangular region of the rectangular patch to the output image
    img2[r2[1]:r2[1] + r2[3], r2[0]:r2[0] + r2[2]] = img2[r2[1]:r2[1] + r2[3], r2[0]:r2[0] + r2[2]] * (
                (1.0, 1.0, 1.0) - mask)

    img2[r2[1]:r2[1] + r2[3], r2[0]:r2[0] + r2[2]] = img2[r2[1]:r2[1] + r2[3], r2[0]:r2[0] + r2[2]] + img2Rect


# Does face extraction and swapping
def extract(src, points_path, step, prev_roi):

    img1Warped = np.copy(src)

    # Set dlib parameters
    predictor_path = 'data/face_features/shape_predictor_68_face_landmarks.dat'
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(predictor_path)

    # detect face src
    rects = detector(src, 1)
    roi = None
    try:
        roi = rects[0]  # region of interest
    except IndexError:
        roi = prev_roi

    shape = predictor(src, roi)
    shape = face_utils.shape_to_np(shape)
    np.savetxt(points_path.format(step=step), shape, fmt="%s")

    # Read array of corresponding points
    points1 = readPoints(points_path.format(step=step))
    points2 = readPoints(points_path.format(step=step))

    # Find convex hull
    hull1 = []
    hull2 = []

    hullIndex = cv.convexHull(np.array(points2), returnPoints=False)

    for i in range(0, len(hullIndex)):
        hull1.append(points1[int(hullIndex[i])])
        hull2.append(points2[int(hullIndex[i])])

    # Find delanauy traingulation for convex hull points
    sizeImg2 = src.shape
    rect = (0, 0, sizeImg2[1], sizeImg2[0])

    dt = calculateDelaunayTriangles(rect, hull2)

    if len(dt) == 0:
        quit()

    # Apply affine transformation to Delaunay triangles
    for i in range(0, len(dt)):
        t1 = []
        t2 = []

        # get points for img1, img2 corresponding to the triangles
        for j in range(0, 3):
            t1.append(hull1[dt[i][j]])
            t2.append(hull2[dt[i][j]])

        warpTriangle(src, img1Warped, t1, t2)

    # Calculate Mask
    hull8U = []
    for i in range(0, len(hull2)):
        hull8U.append((hull2[i][0], hull2[i][1]))

    mask = np.zeros(src.shape, dtype=src.dtype)
    cv.fillConvexPoly(mask, np.int32(hull8U), (255, 255, 255))

    # Clone seamlessly.
    mask_out = cv.subtract(mask, img1Warped)
    mask_out = cv.subtract(mask, mask_out)

    return mask_out, roi


# Read all images for extraction
def make_extraction(path_from, path_to, points_path, path_walk):

    _, _, src_files = next(os.walk(path_walk))
    file_count = len(src_files)
    roi = None
    for i in range(file_count):
        index = src_files[i]
        index = index.split('.')
        index = index[0].split('face')
        index = int(index[1])

        image = cv.imread(path_from.format(img=index))
        image = cv.resize(image, (200, 200))

        # Display the resulting frame
        face, roi = extract(src=image, points_path=points_path, step=index, prev_roi=roi)

        cv.imwrite(path_to.format(step=index), face)

        print("TOTAL - ", file_count, "||| COMPUTED - ", i)


def extract_video(extract_from_video):

    if extract_from_video:
        make_extraction(path_from='data/src/src_video_faces/faces/face_images/src_face{img}.jpg', path_to='data/src/src_landmark/faces/src_face{step}.jpg',
                        points_path="data/src/src_landmark/points/face_points{step}.txt", path_walk='data/src/src_video_faces/faces/face_images/')
        make_extraction(path_from='data/dst/dst_video_faces/faces/face_images/dst_face{img}.jpg', path_to='data/dst/dst_landmark/faces/dst_face{step}.jpg',
                        points_path="data/dst/dst_landmark/points/face_points{step}.txt", path_walk='data/dst/dst_video_faces/faces/face_images/')
    else:
        print("It`s error, bro.")


if __name__ == "__main__":

    extract_from_video = True

    extract_video(extract_from_video)
